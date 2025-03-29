import os
import json
import datetime

def get_sessions_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sessions_dir = os.path.join(base_dir, "sessions")
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    return sessions_dir

def new_session(current_model):
    sessions_dir = get_sessions_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    session_id = f"session_{timestamp}"
    session = {
        "id": session_id,
        "title": f"Session {datetime.datetime.now():%Y-%m-%d %H:%M}",
        "model": current_model if current_model else "",
        "messages": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    return session_id, session

def save_session(session, sessions_dir=None):
    if not sessions_dir:
        sessions_dir = get_sessions_dir()
    session["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_file = os.path.join(sessions_dir, f"{session['id']}.json")
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)

def load_sessions():
    sessions = {}
    sessions_dir = get_sessions_dir()
    session_files = [f for f in os.listdir(sessions_dir) if f.endswith(".json")]
    for file in session_files:
        try:
            with open(os.path.join(sessions_dir, file), "r", encoding="utf-8") as f:
                session_data = json.load(f)
                sessions[session_data["id"]] = session_data
        except Exception as e:
            print(f"Error loading session {file}: {str(e)}")
    return sessions

def load_session(session_id):
    sessions_dir = get_sessions_dir()
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)
            return session_data
    except Exception as e:
        print(f"Error loading session {session_id}: {str(e)}")
        return None

def delete_session(session_id):
    sessions_dir = get_sessions_dir()
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    try:
        if os.path.exists(session_file):
            os.remove(session_file)
            return True
    except Exception as e:
        print(f"Error deleting session {session_id}: {str(e)}")
    return False

def export_session(session, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Session: {session.get('title', 'Untitled')}\n")
            f.write(f"Model: {session.get('model', 'Unknown')}\n")
            f.write(f"Created: {session.get('created_at', '')}\n")
            f.write(f"Updated: {session.get('updated_at', '')}\n")
            f.write("-" * 50 + "\n\n")
            for msg in session.get("messages", []):
                role = "You" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                f.write(f"{role}:\n{content}\n\n")
        return True
    except Exception as e:
        print(f"Error exporting session: {str(e)}")
        return False

def store_message_in_session(session, role, message):
    session["messages"].append({"role": role, "content": message})
    save_session(session)

def get_session_messages(session):
    return session.get("messages", [])
# This file was created by the setup script
