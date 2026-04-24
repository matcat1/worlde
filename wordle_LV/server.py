"""
Latviesu Wordle - Multiplayer Server
Run this once on one machine: python server.py
Both players then connect to this machine's IP.
"""

from flask import Flask, jsonify, request
import random
import threading
from words import WORDY, WORDS

app = Flask(__name__)
lock = threading.Lock()

visi_vardi = set(WORDS)

GREY   = "grey"
GREEN  = "green"
YELLOW = "yellow"


def compute_colours(guess, target):
    colours = [GREY] * 5
    burti = list(target)
    for i in range(5):
        if guess[i] == target[i]:
            colours[i] = GREEN
            burti[i] = None
    for i in range(5):
        if colours[i] == GREEN:
            continue
        if guess[i] in burti:
            colours[i] = YELLOW
            burti[burti.index(guess[i])] = None
    return colours


def fresh_round_state():
    return {
        "target_word":    random.choice(WORDY),
        "written_words":  [],
        "written_colours":[],
        "current_turn":   1,   # whose turn: 1 or 2
        "round_over":     False,
        "round_winner":   None, # player id, or None for draw
    }


state = {
    **fresh_round_state(),
    "scores":        {"1": 0, "2": 0},
    "match_over":    False,
    "match_winner":  None,
    "players_joined": 0,
}


@app.route("/join", methods=["POST"])
def join():
    with lock:
        if state["players_joined"] >= 2:
            return jsonify({"error": "Game full"}), 400
        state["players_joined"] += 1
        pid = state["players_joined"]
        return jsonify({"player_id": pid})


@app.route("/state", methods=["GET"])
def get_state():
    with lock:
        s = dict(state)
        # Only reveal the target word once the round is over
        if not s["round_over"]:
            s = {k: v for k, v in s.items() if k != "target_word"}
        return jsonify(s)


@app.route("/guess", methods=["POST"])
def guess():
    data = request.json
    player_id = data.get("player_id")
    word = data.get("word", "").lower()

    with lock:
        if state["round_over"]:
            return jsonify({"error": "Kārta beigusies"}), 400
        if state["current_turn"] != player_id:
            return jsonify({"error": "Nav tava kārta!"}), 400
        if len(word) != 5:
            return jsonify({"error": "Vajag 5 burtus!"}), 400
        if word not in visi_vardi:
            return jsonify({"error": "Šāda vārda nav!"}), 400

        colours = compute_colours(word, state["target_word"])
        state["written_words"].append(word)
        state["written_colours"].append(colours)

        if all(c == GREEN for c in colours):
            # This player guessed it!
            state["round_over"]   = True
            state["round_winner"] = player_id
            state["scores"][str(player_id)] += 1
            if state["scores"][str(player_id)] >= 3:
                state["match_over"]   = True
                state["match_winner"] = player_id
        elif len(state["written_words"]) >= 6:
            # Used all 6 guesses — draw
            state["round_over"]   = True
            state["round_winner"] = None
        else:
            # Switch turn
            state["current_turn"] = 2 if player_id == 1 else 1

        return jsonify({"ok": True})


@app.route("/next_round", methods=["POST"])
def next_round():
    with lock:
        if not state["round_over"]:
            return jsonify({"error": "Kārta vēl nav beigusies"}), 400

        if state["match_over"]:
            # Reset the whole match
            state["scores"]       = {"1": 0, "2": 0}
            state["match_over"]   = False
            state["match_winner"] = None

        new = fresh_round_state()
        for k, v in new.items():
            state[k] = v

        return jsonify({"ok": True})


if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n=== Latviesu Wordle Serveris ===")
    print(f"Lokālais IP: {local_ip}")
    print(f"Otrs spēlētājs lai izmanto: {local_ip}")
    print(f"Serveris darbojas uz porta 5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
