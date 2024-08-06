from django.conf import settings

# SESSION CONSTANTS
AVAILABLE_SESSION_EXPIRY_TIME = 10  # In seconds
SESSION_BUFFER_TIME = 7  # In seconds

# Withdrawal to play session description
SESSION_WITHDRAWAL_DESCRIPTION = "Withdrawal by user: {} for session id: {}."

# Deposit from winning a session description
SESSION_WIN_DESCRIPION = "Deposit to user: {} for winning {} session"

# Refund for party_a for playing a session description
REFUND_SESSION_DESCRIPTION = "Refund user: {} for playing {} session"

# Partially refund for party_a for playing a session description
PARTIALLY_REFUND_SESSION_DESCRIPTION = (
    "Partially refund user: {} for playing {} session."
)

# Message sent to user on winning a session
SESSION_WIN_MESSAGE = (
    "Congrats, You won KES {} for your {} session. "
    "Seems like you've got the skills - "
    "turn this into a winning streak by playing another session."
)

# Message sent to user on losing a session
SESSION_LOSS_MESSAGE = (
    "You lost {} session to your opponent. "
    "Remember, fall seven times, stand up eight. "
    "Ready for the next challenge?"
)

# Message sent to user on refund
SESSION_REFUND_MESSAGE = (
    f"You've received a {int(settings.SESSION_REFUND_RATIO * 100)}% refund of "
    "KES {} for your {} session. "
    "Time to chase a win in Majibu!"
)

# Message sent to user on partial refund
SESSION_PARTIAL_REFUND_MESSAGE = (
    f"You've received a {int(settings.SESSION_PARTIAL_REFUND_RATIO * 100)}% partial refund of "
    "KES {} for your {} session. "
    "Please attempt atleast one question to be paired or to receive a full refund."
)
