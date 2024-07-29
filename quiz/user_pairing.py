from typing import Iterable

from scipy.stats import skew

from quiz.models import Result


class PairUsers:
    def __init__(self) -> None:
        """Set up initial fields"""
        pass

    def execute_pairing(self, category: str) -> None:
        """Orchestrate the pairing process."""
        self.category = category

        self.queue_ordered_by_exits_at = self.get_category_queue(category=self.category)
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

    def get_category_queue(self, category: str) -> Iterable[Result]:
        """
        Get results for a given category, ordered by `exits_at`.
        """
        return Result.objects.filter(
            is_active=True, session__category=category
        ).order_by("exits_at")

    def reorder_by_score(self, results) -> Iterable[Result]:
        """
        Reorder results by score.
        """
        return results.order_by("score")

    def calculate_skewness(self, results) -> float:
        """
        Calculate skewness for a list of results based on their scores.
        """
        scores = results.values_list("score", flat=True)
        return skew(scores)

    def dynamic_exclusion_percentages(
        self, skewness_value, total_results
    ) -> tuple[int, int]:
        """
        Determine the number of results to exclude from bottom and top based on skewness.
        """
        if skewness_value > 0:  # Right skewed, more high scores
            bottom_exclusion_percentage = max(0, 0.10 - 0.05 * skewness_value)
            top_exclusion_percentage = min(0.20, 0.10 + 0.05 * skewness_value)
        elif skewness_value < 0:  # Left skewed, more low scores
            bottom_exclusion_percentage = min(0.20, 0.10 + 0.05 * abs(skewness_value))
            top_exclusion_percentage = max(0, 0.10 - 0.05 * abs(skewness_value))
        else:  # No skew, balanced performance
            bottom_exclusion_percentage = 0.10
            top_exclusion_percentage = 0.10

        # Normalize to ensure the total exclusion is around 20%
        total_exclusion_percentage = (
            bottom_exclusion_percentage + top_exclusion_percentage
        )

        if total_exclusion_percentage != 0.20:
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
        # Convert results to list for negative indexing
        results_list = list(results)
        to_exclude_bottom = results_list[:bottom_exclusion_count]
        to_exclude_top = results_list[-top_exclusion_count:]

        to_exclude = list(to_exclude_bottom) + list(to_exclude_top)
        to_pair = results_list[bottom_exclusion_count:-top_exclusion_count]

        return to_pair, to_exclude


PairingService = PairUsers()
