from datetime import datetime, timedelta
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from scipy.stats import skew

from commons.constants import DuoSessionStatuses
from commons.raw_logger import logger
from quiz.models import Result
from user_sessions.models import DuoSession

User = get_user_model()


class PairUsers:
    def __init__(self) -> None:
        """Set up initial fields"""
        pass

    def execute_pairing(self, category: str) -> None:
        """Orchestrate the pairing process."""
        logger.info("Executing pairing process...")
        self.category = category

        self.queue_ordered_by_exits_at = self.get_category_queue(category=self.category)

        if self.queue_ordered_by_exits_at.exists():  # type: ignore
            self.queue_ordered_by_score = self.reorder_by_score(
                self.queue_ordered_by_exits_at
            )

            self.skewness = self.calculate_skewness(self.queue_ordered_by_score)
            (
                self.top_exclusion_count,
                self.bottom_exclusion_count,
            ) = self.dynamic_exclusion_percentages(
                self.skewness,
                self.queue_ordered_by_score.count(),  # type: ignore
            )

            self.to_pair, self.to_exclude = self.get_exclusions(
                self.queue_ordered_by_score,
                self.bottom_exclusion_count,
                self.top_exclusion_count,
            )

            self.pair_instances(
                queue_ordered_by_exits_at=self.queue_ordered_by_exits_at,
                queue_ordered_by_score=self.queue_ordered_by_score,
            )

    def get_category_queue(self, category: str) -> Iterable[Result]:
        """
        Get results for a given category, ordered by `exits_at`.
        """
        logger.info(f"Creating queue for {category}")
        return Result.objects.filter(
            is_active=True, session__category=category
        ).order_by("exits_at")

    def reorder_by_score(self, results) -> Iterable[Result]:
        """
        Reorder results by score.
        """
        logger.info("Re-ordering queue by score.")
        return results.order_by("score")

    def calculate_skewness(self, results) -> float:
        """
        Calculate skewness for a list of results based on their scores.
        """
        logger.info("Calculating skewness")
        # Iterate through the QuerySet and add scores to the list
        scores = [float(result.score) for result in results]
        return skew(scores)

    def dynamic_exclusion_percentages(
        self, skewness_value, total_results
    ) -> tuple[int, int]:
        """
        Determine the number of results to exclude from bottom and top based on skewness.
        """
        if skewness_value > 0:  # Right skewed, more high scores
            logger.info(
                f"Scores are right-skewed (have more high scores): {skewness_value}"
            )
            bottom_exclusion_percentage = max(0, 0.10 - 0.05 * skewness_value)
            top_exclusion_percentage = min(0.20, 0.10 + 0.05 * skewness_value)
        elif skewness_value < 0:  # Left skewed, more low scores
            logger.info(
                f"Scores are left-skewed (have more low scores): {skewness_value}"
            )
            bottom_exclusion_percentage = min(0.20, 0.10 + 0.05 * abs(skewness_value))
            top_exclusion_percentage = max(0, 0.10 - 0.05 * abs(skewness_value))
        else:  # No skew, balanced performance
            logger.info(f"Scores are balanced: {skewness_value}")
            bottom_exclusion_percentage = 0.10
            top_exclusion_percentage = 0.10

        # Normalize to ensure the total exclusion is around 20%
        total_exclusion_percentage = (
            bottom_exclusion_percentage + top_exclusion_percentage
        )

        if total_exclusion_percentage != 0.20:
            logger.info("Adjusting exclusion percentages.")
            adjustment_factor = 0.20 / total_exclusion_percentage
            bottom_exclusion_percentage *= adjustment_factor
            top_exclusion_percentage *= adjustment_factor

        # Calculate number of scores to exclude
        bottom_exclusion_count = int(bottom_exclusion_percentage * total_results)
        top_exclusion_count = int(top_exclusion_percentage * total_results)

        return bottom_exclusion_count, top_exclusion_count

    def get_exclusions(
        self, results, bottom_exclusion_count, top_exclusion_count
    ) -> tuple[list, list]:
        """
        Determine which results to exclude from the bottom and top.
        """
        logger.info(
            f"Bottom exclusion count: {bottom_exclusion_count}. Top exclusion count: {top_exclusion_count}"
        )
        # Convert results to list for negative indexing
        results_list = list(results)
        to_exclude_bottom = results_list[:bottom_exclusion_count]
        to_exclude_top = results_list[-top_exclusion_count:]

        to_exclude = list(to_exclude_bottom) + list(to_exclude_top)
        to_pair = results_list[bottom_exclusion_count:-top_exclusion_count]

        return to_pair, to_exclude

    def is_ready_for_pairing(self, result) -> bool:
        """
        Check if the result instance meets the criteria to search for another instance to pair with.
        """
        logger.info(f"Checking if result id: {result.id} is ready for pairing.")
        current_time = datetime.now()
        time_5_minutes_later = current_time + timedelta(minutes=5)

        # Check if the exits_at value has already passed
        if (
            result.exits_at <= current_time
            or
            # Check if the exits_at value is within the next 5 minutes (that is, is the instance about to exit)
            current_time <= result.exits_at <= time_5_minutes_later
        ):
            return True

        return False

    def is_partial_refund(self, result) -> bool:
        """If a user played a session, but did not answer at least one question, we do a partial refund.
        To receive a full refund, attempt to answer atleast one question, no matter if it is correct or wrong.
        """
        logger.info(f"Checking if result id: {result.id} is a partial refund.")
        if result.total_answered == 0:  # User did not answer atleast one question
            return True

        return False

    def is_full_refund(self, result) -> bool:
        """If the exit_at field is past the current time, simply refund the user
        and do not search for an instance to pair with."""
        logger.info(f"Checking if result id: {result.id} is a full refund.")
        if (
            result.exits_at < datetime.now()  # If exit_at field is past current time
            or result in self.to_exclude  # Or if result does not meet pairing threshold
        ):
            return True
        return False

    def find_closest_instance(self, target_instance, instances) -> Result | None:
        """
        Find the instance with the closest score to the target_instance from the given instances.
        """
        logger.info(f"Searching for the closest instance to {target_instance.id}")
        target_score = target_instance.score
        closest_instance = None
        closest_score_diff = float("inf")

        for instance in instances:
            score_diff = abs(instance.score - target_score)

            if score_diff < closest_score_diff:
                closest_score_diff = score_diff
                closest_instance = instance

        if closest_instance:
            if (
                # In some edge cases caused by delayed or failed celery tasks, a user can have two active results.
                # The below if statement prevents a user from being paired to their previous result instance.
                instance.user == closest_instance.user
                or
                # If closest_instance is eligible for a full refund
                closest_instance in self.to_exclude
                or
                # If closest_instance has the same score, fully refund the target_instance
                closest_instance.score == target_instance.score
                or
                # If closest_instance has not answered any question. That is, closest instance
                # should be partially refunded.
                closest_instance.total_answered == 0
            ):
                logger.info(f"No close instance found for {target_instance.id}")
                closest_instance = None

        return closest_instance

    def deactivate_instances(self, instances) -> None:
        """Deactivate instances so that they're not used in the pairing process again."""
        logger.info("Deactivating result instances...")
        result_ids = [result.id for result in instances]
        # Bulk update is_active to False
        Result.objects.filter(id__in=result_ids).update(is_active=False)

    def pair_instances(
        self, *, queue_ordered_by_exits_at, queue_ordered_by_score
    ) -> None:
        logger.info("Starting pair instances service...")
        for result in queue_ordered_by_exits_at:
            # Re-set default values:
            winner, party_a, party_b = None, None, None
            duo_session_status = None
            instances_to_deactivate = []

            # Note that the queue_ordered_by_score is modified inside the loop
            # The if statement below prevents errors
            if result in queue_ordered_by_score and self.is_ready_for_pairing(result):
                party_a = result
                # Remove the instance from the score-ordered queue
                queue_ordered_by_score = queue_ordered_by_score.exclude(id=result.id)

                if self.is_partial_refund(result):
                    duo_session_status = DuoSessionStatuses.PARTIALLY_REFUNDED.value
                    instances_to_deactivate = [party_a]

                elif self.is_full_refund(result):
                    duo_session_status = DuoSessionStatuses.REFUNDED.value
                    instances_to_deactivate = [party_a]

                else:
                    # Find the next instance with the closest score
                    closest_instance = self.find_closest_instance(
                        result, queue_ordered_by_score
                    )

                    if closest_instance:
                        # Pop closest instance from queue
                        queue_ordered_by_score.exclude(id=closest_instance.id)
                        winner = self.get_winner(result, closest_instance)
                        party_b = closest_instance

                        duo_session_status = DuoSessionStatuses.PAIRED.value
                        instances_to_deactivate = [party_a, party_b]

                    else:
                        duo_session_status = DuoSessionStatuses.REFUNDED.value
                        instances_to_deactivate = [party_a]

                self.deactivate_instances(instances_to_deactivate)
                self.create_duo_session(
                    party_a=party_a.user,
                    party_b=party_b.user if party_b else None,
                    session=party_a.session,
                    duo_session_status=duo_session_status,
                    winner=winner.user if winner else None,
                )

    def get_winner(self, party_a, party_b) -> Result:
        """Return the winner between two result instances"""
        logger.info(f"Getting winner between results {party_a.id} and {party_b.id}")
        if party_a.score > party_b.score:
            return party_a
        else:
            return party_b

    def create_duo_session(
        self,
        *,
        party_a,
        party_b,
        winner,
        session,
        duo_session_status: str,
    ) -> None:
        """Create a DuoSession instance.
        This is the final step before funding wallets."""
        logger.info(f"Creating duo session with status: {duo_session_status}")
        DuoSession.objects.create(
            party_a=party_a,
            party_b=party_b,
            session=session,
            amount=settings.SESSION_STAKE,
            status=duo_session_status,
            winner=winner,
        )


PairingService = PairUsers()
