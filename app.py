from flask import Flask, render_template, session, redirect, url_for, request
import random
import csv
import ipdb

app = Flask(__name__, static_folder="assets", template_folder="templates")
app.secret_key = "wedding_mystery_secret"

# Load characters and their descriptions
characters = []
special_powers = {}
used_characters = []
eliminated_players = []

with open('Wedding_Game_Characters(2).csv', 'r') as char_file:
    reader = csv.DictReader(char_file)
    for row in reader:
        characters.append({
            "id": row["ID"],
            "name": row["Character"],
            "bio": row["Bio"],
            "gender": row["Gender"],
            "role": row["Role"],
            "special_power_name": row["Special Power Name"],
            "special_power_description": row["Special Power Description"],
            "is_active": False,
        })

tasks = {
    "Killer": [
        "Convincere un invitato a lasciare la stanza per 5 minuti.",
        "Far compiere un'azione sospetta a un invitato.",
        "Nascondere un oggetto importante e farlo cercare.",
    ],
    "Ospite": [
        "Trovare tre oggetti sospetti nascosti nella stanza.",
        "Parlare con altri invitati e scoprire i loro ruoli.",
        "Risolvi un enigma: qual è l'oggetto più importante del matrimonio?",
    ],
}

progress_data = []
special_abilities = []


@app.route("/")
def home():
    if "character" in session and "role" in session:
        assigned = True
        character = session["character"]
        role = session["role"]
    else:
        assigned = False
        character = None
        role = None
    return render_template("index.html", assigned=assigned, character=character, role=role)


@app.route("/select_gender", methods=["POST"])
def select_gender():
    gender = request.form.get("gender")
    session["gender"] = gender  # Save gender in session
    return redirect(url_for("assign_character"))


@app.route("/assign_character")
def assign_character():
    if "character" not in session and "role" not in session:
        available_characters = [
            char for char in characters if char["gender"] == session["gender"] and char["name"] not in used_characters
        ]

        if not available_characters:
            return "No characters left for the selected gender!", 400

        chosen_character = random.choice(available_characters)
        used_characters.append(chosen_character["name"])
        random_role = "Killer" if random.random() < 0.2 else "Ospite"

        session["character"] = chosen_character["name"]
        session["role"] = random_role

        victim = None
        if random_role == "Killer":
            victim = assign_victim()

        progress_data.append({
            "character": chosen_character["name"],
            "role": random_role,
            "completed_tasks": 0,
            "total_tasks": len(tasks[random_role]),
            "victim": victim
        })

    return redirect(url_for("tasks_page", role=session["role"], character=session["character"]))


def assign_victim():
    available_victims = [
        player["character"] for player in progress_data
        if player["role"] == "Ospite" and player["character"] not in eliminated_players
    ]
    return available_victims[0] if available_victims else None


@app.route("/eliminate_victim", methods=["POST"])
def eliminate_victim():
    killer = request.form.get("killer")
    victim = request.form.get("victim")

    if victim:
        eliminated_players.append(victim)
        progress_data[:] = [player for player in progress_data if player["character"] != victim]

    for player in progress_data:
        if player["character"] == killer and player["role"] == "Killer":
            player["victim"] = assign_victim()
            break

    return redirect(url_for("tasks_page", role=session["role"], character=killer))


@app.route("/tasks/<role>/<character>")
def tasks_page(role, character):
    special_move_used = any(ability["character"] == character for ability in special_abilities)

    special_ability_used = None
    if special_move_used:
        for ability in special_abilities:
            if ability["character"] == character:
                special_ability_used = ability["ability"]
                break

    victim = None
    for player in progress_data:
        if player["character"] == character and player["role"] == "Killer":
            victim = player.get("victim")
            break

    character_name = character

    return render_template(
        "tasks.html",
        role=role,
        character=character,
        tasks=tasks[role],
        special_move_used=special_move_used,
        special_ability_used=special_ability_used,
        victim=victim,
        special_power = [character["special_power_name"] for character in characters if character["name"] == character_name]
    )


@app.route("/use_special", methods=["POST"])
def use_special():
    character = request.form.get("character")
    role = request.form.get("role")
    character_name = character

    if any(ability["character"] == character for ability in special_abilities):
        return redirect(url_for("tasks_page", role=role, character=character))

    ability = [character["special_power_name"] for character in characters if character["name"] == character_name]
    special_abilities.append({"character": character, "ability": ability})

    return redirect(url_for("tasks_page", role=role, character=character))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", progress_data=progress_data, special_abilities=special_abilities)


@app.route("/reset")
def reset_game():
    session.clear()
    progress_data.clear()
    special_abilities.clear()
    used_characters.clear()
    eliminated_players.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)