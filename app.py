from flask import Flask, render_template, request, session
import random

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret"  # for session support


WINNING_COMBOS = [
    (0, 1, 2),  # rows
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),  # columns
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),  # diagonals
    (2, 4, 6),
]


def get_winning_combo(board, player):
    """Return the winning combo (tuple of indices) if player wins, else None."""
    for a, b, c in WINNING_COMBOS:
        if board[a] == board[b] == board[c] == player:
            return (a, b, c)
    return None


def check_winner(board, player):
    """Return True if the given player has won."""
    return get_winning_combo(board, player) is not None


def check_draw(board):
    """Return True if the board is full and there is no winner."""
    return all(spot != " " for spot in board)


def get_computer_move(board, difficulty):
    """
    Choose the best position for the computer (O) based on difficulty.

    difficulty: "amateur", "intermediate", "expert"
    """
    computer = "O"
    human = "X"
    empty_positions = [i for i, spot in enumerate(board) if spot == " "]

    # --- Amateur: purely random ---
    if difficulty == "amateur":
        return random.choice(empty_positions)

    # --- Intermediate & Expert share win/block logic ---
    # 1) Try to win
    for pos in empty_positions:
        board[pos] = computer
        if check_winner(board, computer):
            board[pos] = " "
            return pos
        board[pos] = " "

    # 2) Block human's win
    for pos in empty_positions:
        board[pos] = human
        if check_winner(board, human):
            board[pos] = " "
            return pos
        board[pos] = " "

    # For intermediate, stop here and just pick random
    if difficulty == "intermediate":
        return random.choice(empty_positions)

    # --- Expert only (extra strategy) ---
    # 3) Take center
    if 4 in empty_positions:
        return 4

    # 4) Take a corner
    corners = [0, 2, 6, 8]
    available_corners = [c for c in corners if c in empty_positions]
    if available_corners:
        return random.choice(available_corners)

    # 5) Random move
    return random.choice(empty_positions)


@app.route("/", methods=["GET", "POST"])
def index():
    # Session-based scoreboard
    scores = session.get("scores", {"X": 0, "O": 0, "draw": 0})

    # Default state
    board_str = " " * 9
    board = list(board_str)
    current_player = "X"
    opponent_type = "human"
    difficulty = "amateur"
    game_over = False
    message = "Choose mode and start a game."
    winner = None
    winning_combo = None  # tuple of indices or None

    if request.method == "POST":
        action = request.form.get("action", "start")

        # Reset scoreboard
        if action == "reset_scores":
            scores = {"X": 0, "O": 0, "draw": 0}
            session["scores"] = scores
            message = "Scoreboard reset. Start a new game!"
            game_over = True  # nothing on the board
            board = [" "] * 9

        # Start a new match (keep scores)
        elif action == "start":
            opponent_type = request.form.get("mode", "human")
            difficulty = request.form.get("difficulty", "amateur")
            board = [" "] * 9
            current_player = "X"
            game_over = False
            winner = None
            winning_combo = None

            if opponent_type == "computer":
                message = f"New game: You (X) vs Computer (O) – {difficulty.title()}"
            else:
                message = "New game: Player X vs Player O"

        # A move has been played
        elif action == "move":
            board_str = request.form.get("board", " " * 9)
            board = list(board_str)
            current_player = request.form.get("current_player", "X")
            opponent_type = request.form.get("opponent_type", "human")
            difficulty = request.form.get("difficulty", "amateur")
            game_over = request.form.get("game_over", "false") == "true"
            message = ""
            winner = None
            winning_combo = None

            if not game_over:
                # Player's move
                move_index = int(request.form["move"])
                if board[move_index] == " ":
                    board[move_index] = current_player

                    # Check if player wins
                    combo = get_winning_combo(board, current_player)
                    if combo:
                        game_over = True
                        winner = current_player
                        winning_combo = combo
                        scores[current_player] += 1
                        if opponent_type == "computer" and current_player == "O":
                            message = "🤖 Computer wins!"
                        elif opponent_type == "computer" and current_player == "X":
                            message = "🎉 You win!"
                        else:
                            message = f"🎉 Player {current_player} wins!"
                    elif check_draw(board):
                        game_over = True
                        winner = "draw"
                        scores["draw"] += 1
                        message = "It's a draw!"
                    else:
                        # No winner yet: next turn
                        if opponent_type == "computer" and current_player == "X":
                            # Computer's turn
                            ai_index = get_computer_move(board, difficulty)
                            board[ai_index] = "O"

                            combo_ai = get_winning_combo(board, "O")
                            if combo_ai:
                                game_over = True
                                winner = "O"
                                winning_combo = combo_ai
                                scores["O"] += 1
                                message = "🤖 Computer wins!"
                            elif check_draw(board):
                                game_over = True
                                winner = "draw"
                                scores["draw"] += 1
                                message = "It's a draw!"
                            else:
                                current_player = "X"
                                message = "Your turn (X)."
                        else:
                            # Player vs Player: switch player
                            current_player = "O" if current_player == "X" else "X"
                            message = f"Player {current_player}'s turn."
                else:
                    message = "That spot is already taken. Choose another."
            else:
                message = "Game is already over. Start a new game."

    # Save updated scores back into session
    session["scores"] = scores

    # Rebuild board_str to pass into hidden input
    board_str = "".join(board)

    return render_template(
        "index.html",
        board=board,
        board_str=board_str,
        current_player=current_player,
        opponent_type=opponent_type,
        difficulty=difficulty,
        game_over=game_over,
        message=message,
        scores=scores,
        winner=winner,
        winning_combo=winning_combo,
    )


if __name__ == "__main__":
    app.run(debug=True)