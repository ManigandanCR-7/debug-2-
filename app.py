import re
import difflib
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)


# ============================================================
# DEFAULT / REGISTERED CODE FOR EACH CODE EDITOR
# ============================================================

REGISTERED_CODES = {

    # --------------------------------------------------------
    # CODE EDITOR 1
    # Outer app/__init__.py
    # --------------------------------------------------------
    "editor1": r'''import os

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from app.gmail import (
    is_email_command,
    extract_email,
    create_gmail_url,
    generate_email_with_gemini
)

from app.youtube import youtube_bp


def create_app():

    app = Flask(__name__)

    CORS(app)


    # YouTube
    app.register_blueprint(
        youtube_bp,
        url_prefix="/youtube"
    )


    # Home
    @app.route("/")
    def home():

        return render_template("index.html")


    # HTML
    @app.route("/html")
    def html():

        return render_template("index.html")


    # Health
    @app.route("/health")
    def health():

        return jsonify({
            "status": "ok",
            "service": "Nova AI Agent"
        })


    # Gmail AI Agent
    @app.route("/agent", methods=["POST"])
    def agent():

        try:

            data = request.get_json(
                silent=True
            ) or {}

            command = data.get(
                "command",
                ""
            ).strip()


            if not command:

                return jsonify({
                    "success": False,
                    "message": "Command is required"
                }), 400


            if not is_email_command(command):

                return jsonify({
                    "success": False,
                    "message": "Please give a Gmail command."
                }), 400


            recipient = extract_email(
                command
            )


            email = generate_email_with_gemini(
                command
            )


            return jsonify({

                "success": True,

                "type": "email",

                "email_generated": True,

                "recipient": recipient,

                "subject": email["subject"],

                "body": email["body"],

                "gmail_url": create_gmail_url(
                    email["subject"],
                    email["body"],
                    recipient
                )
            })


        except Exception as e:

            return jsonify({
                "success": False,
                "message": str(e)
            }), 500


    return app''',


    # --------------------------------------------------------
    # CODE EDITOR 2
    # app/gmail/__init__.py
    # --------------------------------------------------------
    "editor2": r'''from .gmail_write import is_email_command, extract_email, create_gmail_url
from .gmail_gen import generate_email_with_gemini''',


    # --------------------------------------------------------
    # CODE EDITOR 3
    # app/gmail/gmail_gen.py

    # --------------------------------------------------------
    "editor3": r'''import os
import json
import re
import time
import random
import urllib.request
import urllib.error

API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

def generate_email_with_gemini(command):
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    prompt = f"""
You are a professional Gmail email writing assistant.

Convert the user's voice command into a professional email.

Rules:
- Do not copy the command literally.
- Do not explain anything.
- Do not invent names, dates, prices, companies, attachments, or facts.
- Keep the email natural and concise.
- Include an appropriate greeting and closing.

Output exactly:

SUBJECT: <subject>
BODY:
<email body>

User command:
{command}
"""

    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL}:generateContent"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())

            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = re.sub(r"```(?:text)?|```", "", text).strip()

            subject = re.search(r"SUBJECT:\s*(.+)", text, re.I)
            body = re.search(r"BODY:\s*([\s\S]+)", text, re.I)

            if not subject or not body:
                raise RuntimeError("Gemini returned an invalid email format.")

            return {
                "subject": subject.group(1).strip(),
                "body": body.group(1).strip()
            }

        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                try:
                    detail = e.read().decode()
                except Exception:
                    detail = str(e)
                raise RuntimeError(f"Gemini API error: {detail}")

            time.sleep((2 ** attempt) + random.random())

        except Exception:
            if attempt == 3:
                raise
            time.sleep(1)''',


    # --------------------------------------------------------
    # CODE EDITOR 4
    # app/gmail/gmail_write.py
    # --------------------------------------------------------
    "editor4": r'''import os
import re
import urllib.parse


KEYWORDS = (
    "gmail", "email", "e-mail", "mail",
    "write an email", "send an email", "draft an email",
    "compose an email", "write mail", "send mail", "draft mail",
    "compose mail"
)

def is_email_command(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)

def extract_email(text):
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    if match:
        return match.group(0)

    match = re.search(
        r"([\w.+-]+)\s+at\s+([\w.-]+)\s+dot\s+(\w+)",
        text.lower()
    )
    if match:
        return f"{match.group(1)}@{match.group(2)}.{match.group(3)}"

    return ""

def create_gmail_url(subject="", body="", recipient=""):
    params = urllib.parse.urlencode({
        "view": "cm",
        "fs": "1",
        "to": recipient,
        "su": subject,
        "body": body
    })
    return f"https://mail.google.com/mail/u/0/?{params}"''',


    # --------------------------------------------------------
    # CODE EDITOR 5
    # templates/index.html
    # --------------------------------------------------------
    "editor5": r'''<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>Nova AI</title>


<style>

body{

    margin:0;

    height:100vh;

    display:grid;

    place-items:center;

    background:#111;

    color:white;

    font-family:Arial;
}


.card{

    width:400px;

    padding:25px;

    text-align:center;

    background:#222;

    border:1px solid #444;

    border-radius:10px;
}


.mic{

    width:75px;

    height:75px;

    border:0;

    border-radius:50%;

    font-size:30px;

    cursor:pointer;

    background:#eee;
}


.mic.listening{

    background:#aaa;
}


.status{

    margin:15px;

    color:#aaa;
}


.command{

    margin:10px;

    color:#ccc;
}


.editor{

    display:none;

    margin-top:20px;

    text-align:left;
}


.recipient{

    color:#aaa;

    font-size:13px;
}


input,
textarea{

    width:100%;

    margin:6px 0;

    padding:10px;

    box-sizing:border-box;

    background:#111;

    color:white;

    border:1px solid #444;

    border-radius:5px;
}


textarea{

    height:130px;

    resize:vertical;
}


button.action{

    padding:10px 14px;

    margin-top:5px;

    border:0;

    border-radius:5px;

    cursor:pointer;
}


.primary{

    background:#666;

    color:white;
}

</style>

</head>


<body>


<div class="card">


<h2>Nova AI</h2>


<p>
    Say a song name or create an email
</p>


<button
    id="mic"
    class="mic"
>
    🎙️
</button>


<div
    id="status"
    class="status"
>
    Tap microphone
</div>


<div
    id="command"
    class="command"
></div>



<!-- Gmail Editor -->

<div
    id="editor"
    class="editor"
>


    <div
        id="recipient"
        class="recipient"
    ></div>


    <input
        id="subject"
        placeholder="Email subject"
    >


    <textarea
        id="body"
        placeholder="Email body"
    ></textarea>


    <button
        id="open"
        class="action primary"
    >
        Open in Gmail
    </button>


    <button
        id="regen"
        class="action"
    >
        Regenerate
    </button>


</div>


</div>



<script>


// --------------------------------------------------
// DOM REFERENCES
// --------------------------------------------------

const $ =
    id => document.getElementById(id);


const mic =
    $("mic");


const status =
    $("status");


const commandBox =
    $("command");


const editor =
    $("editor");


const recipient =
    $("recipient");


const subject =
    $("subject");


const body =
    $("body");



// --------------------------------------------------
// SPEECH RECOGNITION
// --------------------------------------------------

const SR =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


let recognition;

let listening = false;



// --------------------------------------------------
// COMMAND STATE
// --------------------------------------------------

let lastCommand = "";


// Prevent duplicate email generation

let emailGenerated = false;


// Prevent multiple requests at the same time

let generatingEmail = false;


// YouTube tab

let youtubeTab = null;



// --------------------------------------------------
// SPEECH RECOGNITION SETUP
// --------------------------------------------------

if(!SR){

    status.textContent =
        "Speech recognition unavailable";

    mic.disabled = true;

}
else{

    recognition =
        new SR();


    recognition.lang =
        "en-US";


    recognition.continuous =
        false;


    recognition.interimResults =
        false;



    recognition.onstart = () => {

        listening = true;

        mic.classList.add(
            "listening"
        );

        status.textContent =
            "Listening...";

    };



    recognition.onend = () => {

        listening = false;

        mic.classList.remove(
            "listening"
        );

    };



    recognition.onerror = e => {

        listening = false;

        mic.classList.remove(
            "listening"
        );

        status.textContent =
            "Voice error: " +
            e.error;

    };



    recognition.onresult = e => {

        const text =
            e.results[0][0]
            .transcript
            .trim();


        if(!text){

            status.textContent =
                "No command detected";

            return;

        }


        lastCommand =
            text;


        commandBox.textContent =
            text;


        processCommand(
            text
        );

    };



    mic.onclick = () => {

        if(listening)
            return;


        try{

            recognition.start();

        }
        catch(e){

            console.log(e);

        }

    };

}



// --------------------------------------------------
// GMAIL KEYWORD DETECTION
// --------------------------------------------------
//
// Gmail requires BOTH:
//
// create
// email
//
// Examples:
//
// "create email for my boss"
// "create an email for my manager"
//
// --------------------------------------------------

function isGmail(command){

    const hasCreate =
        /\bcreate\b/i.test(command);


    const hasEmail =
        /\bemail\b/i.test(command);


    return (
        hasCreate &&
        hasEmail
    );

}



// --------------------------------------------------
// YOUTUBE KEYWORD DETECTION
// --------------------------------------------------
//
// YouTube requires:
//
// play
//
// OR
//
// song
//
// Examples:
//
// "play believer"
// "play a song"
// "song believer"
//
// --------------------------------------------------

function isYouTube(command){

    return (
        /\bplay\b/i.test(command) ||
        /\bsong\b/i.test(command)
    );

}



// --------------------------------------------------
// MAIN COMMAND PROCESSOR
// --------------------------------------------------

async function processCommand(command){


    // ----------------------------------------------
    // CHECK COMMAND TYPE
    // ----------------------------------------------

    const gmail =
        isGmail(command);


    const youtube =
        isYouTube(command);



    // ----------------------------------------------
    // GMAIL COMMAND
    // ----------------------------------------------

    if(gmail){

        // Prevent duplicate generation

        if(generatingEmail){

            status.textContent =
                "Email is already being generated...";

            return;

        }


        // Prevent the same command from generating
        // another email

        if(
            emailGenerated &&
            command === lastCommand
        ){

            status.textContent =
                "Email already generated.";

            return;

        }


        generatingEmail = true;


        status.textContent =
            "Generating email...";


        try{


            const response =
                await fetch(
                    "/agent",
                    {

                        method:"POST",

                        headers:{
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                command:command
                            })

                    }
                );



            const data =
                await response.json();



            if(
                !response.ok ||
                !data.success
            ){

                throw Error(
                    data.message ||
                    "Email request failed"
                );

            }



            // Show ONE generated email

            showEmail(
                data
            );


            emailGenerated = true;


        }
        catch(error){

            console.error(
                error
            );


            status.textContent =
                error.message ||
                "Email generation failed";

        }
        finally{

            generatingEmail = false;

        }


        return;

    }



    // ----------------------------------------------
    // YOUTUBE COMMAND
    // ----------------------------------------------

    else if(youtube){

        status.textContent =
            "Finding song...";


        try{


            const response =
                await fetch(
                    "/youtube/play",
                    {

                        method:"POST",

                        headers:{
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                command:command
                            })

                    }
                );



            const data =
                await response.json();



            if(
                !response.ok ||
                !data.success
            ){

                throw Error(
                    data.message ||
                    "YouTube request failed"
                );

            }



            playYouTube(
                data
            );


        }
        catch(error){

            console.error(
                error
            );


            status.textContent =
                error.message ||
                "YouTube request failed";

        }


        return;

    }



    // ----------------------------------------------
    // UNKNOWN COMMAND
    // ----------------------------------------------

    else{

        status.textContent =
            "Please say 'create email' or 'play song'.";

        return;

    }

}



// --------------------------------------------------
// SHOW GENERATED EMAIL
// --------------------------------------------------

function showEmail(data){


    recipient.dataset.email =
        data.recipient || "";


    recipient.textContent =
        data.recipient
        ? "To: " + data.recipient
        : "Recipient not specified";


    subject.value =
        data.subject || "";


    body.value =
        data.body || "";


    editor.style.display =
        "block";


    status.textContent =
        "Email ready. Review or edit it.";

}



// --------------------------------------------------
// OPEN GMAIL
// --------------------------------------------------

$("open").onclick = () => {


    const url =
        "https://mail.google.com/mail/u/0/?" +

        new URLSearchParams({

            view:"cm",

            fs:"1",

            to:
                recipient.dataset.email || "",

            su:
                subject.value,

            body:
                body.value

        });



    const win =
        window.open(
            url,
            "NovaGmail"
        );



    if(!win){

        status.textContent =
            "Please allow popups for this site.";

    }

};



// --------------------------------------------------
// REGENERATE BUTTON
// --------------------------------------------------
//
// No automatic second generation.
//
// Clicking this button also does NOT call /agent.
// --------------------------------------------------

$("regen").onclick = () => {

    status.textContent =
        "Email already generated. Edit the existing email.";

};



// --------------------------------------------------
// YOUTUBE PLAYBACK
// --------------------------------------------------

function playYouTube(data){


    if(
        !youtubeTab ||
        youtubeTab.closed
    ){

        youtubeTab =
            window.open(
                data.url,
                "NovaYouTube"
            );

    }
    else{

        youtubeTab.location.href =
            data.url;

        youtubeTab.focus();

    }


    status.textContent =
        "Playing";

}


</script>


</body>

</html>'''
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_char_diffs(expected: str, found: str):
    """
    Finds exact character differences between
    expected and submitted strings.
    """

    diffs = []

    matcher = difflib.SequenceMatcher(
        None,
        expected,
        found
    )

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "replace":

            diffs.append(
                f"Expected '{expected[i1:i2]}', "
                f"found '{found[j1:j2]}' "
                f"at character index {j1}"
            )

        elif tag == "delete":

            diffs.append(
                f"Missing character(s) "
                f"'{expected[i1:i2]}' "
                f"near index {j1}"
            )

        elif tag == "insert":

            diffs.append(
                f"Extra character(s) "
                f"'{found[j1:j2]}' "
                f"at index {j1}"
            )

    return diffs


def strip_all_whitespace(text: str):
    """
    Removes spaces and tabs so inner spacing
    can be ignored during comparison.
    """

    return re.sub(
        r"[ \t]+",
        "",
        text
    )


# ============================================================
# CODE COMPARISON
# ============================================================

def analyze_differences(
    registered: str,
    submitted: str
):

    reg_lines = (
        registered
        .replace("\xa0", " ")
        .replace("\r\n", "\n")
        .splitlines()
    )

    sub_lines = (
        submitted
        .replace("\xa0", " ")
        .replace("\r\n", "\n")
        .splitlines()
    )

    if not any(sub_lines):

        return {
            "match": False,
            "errors": [
                {
                    "type": "empty",
                    "message": "Submitted code is empty."
                }
            ]
        }

    errors = []

    for line_idx in range(
        1,
        len(sub_lines) + 1
    ):

        if line_idx > len(reg_lines):

            errors.append({
                "line_no": line_idx,
                "type": "extra_line",
                "message": (
                    f"Line {line_idx} is an extra line "
                    "not present in registered code."
                ),
                "found": sub_lines[line_idx - 1]
            })

            continue

        expected_line = reg_lines[
            line_idx - 1
        ]

        sub_line = sub_lines[
            line_idx - 1
        ]

        expected_indent = (
            len(expected_line)
            - len(expected_line.lstrip(" "))
        )

        found_indent = (
            len(sub_line)
            - len(sub_line.lstrip(" "))
        )

        expected_content = strip_all_whitespace(
            expected_line
        )

        found_content = strip_all_whitespace(
            sub_line
        )

        if (
            expected_indent == found_indent
            and expected_content == found_content
        ):
            continue

        line_error = {
            "line_no": line_idx,
            "indentation": None,
            "character_mismatches": [],
            "expected_line": expected_line,
            "found_line": sub_line
        }

        if expected_indent != found_indent:

            diff_spaces = (
                expected_indent
                - found_indent
            )

            if diff_spaces > 0:

                indent_msg = (
                    f"Needs {diff_spaces} more "
                    "leading space(s) "
                    f"(Expected {expected_indent}, "
                    f"found {found_indent})."
                )

            else:

                indent_msg = (
                    f"Has {abs(diff_spaces)} extra "
                    "leading space(s) "
                    f"(Expected {expected_indent}, "
                    f"found {found_indent})."
                )

            line_error["indentation"] = {
                "expected_spaces": expected_indent,
                "found_spaces": found_indent,
                "message": indent_msg
            }

        if expected_content != found_content:

            line_error["character_mismatches"] = (
                get_char_diffs(
                    expected_content,
                    found_content
                )
            )

        if (
            line_error["indentation"]
            or line_error["character_mismatches"]
        ):

            errors.append(line_error)

    return {
        "match": len(errors) == 0,
        "errors": errors
    }


# ============================================================
# FULL CODE FIX
# ============================================================

def fix_full_code(editor_id):

    """
    Completely replaces the selected editor's code
    with its registered/default code.
    """

    if editor_id not in REGISTERED_CODES:

        return {
            "success": False,
            "message": "Invalid editor ID.",
            "fixed_code": ""
        }

    fixed_code = REGISTERED_CODES[
        editor_id
    ]

    return {
        "success": True,
        "editor_id": editor_id,
        "fixed_code": fixed_code,
        "changed_count": 1,
        "message": (
            f"{editor_id} has been restored "
            "to the default code."
        )
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# COMPARE
# ============================================================

@app.route(
    "/compare",
    methods=["POST"]
)
def compare():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    editor_id = data.get(
        "editor_id"
    )

    input_code = data.get(
        "input_code",
        ""
    )

    if editor_id not in REGISTERED_CODES:

        return jsonify({
            "match": False,
            "errors": [
                {
                    "type": "invalid_editor",
                    "message": "Invalid editor ID."
                }
            ]
        }), 400

    result = analyze_differences(
        REGISTERED_CODES[editor_id],
        input_code
    )

    result["editor_id"] = editor_id

    return jsonify(result)


# ============================================================
# FIX
# ============================================================

@app.route(
    "/fix",
    methods=["POST"]
)
def fix():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    editor_id = data.get(
        "editor_id"
    )

    if editor_id not in REGISTERED_CODES:

        return jsonify({
            "success": False,
            "message": "Invalid editor ID."
        }), 400

    result = fix_full_code(
        editor_id
    )

    return jsonify(result)


# ============================================================
# OLD FIX-INDENTATION ROUTE
# ============================================================

@app.route(
    "/fix-indentation",
    methods=["POST"]
)
def fix_indentation():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    editor_id = data.get(
        "editor_id"
    )

    if editor_id not in REGISTERED_CODES:

        return jsonify({
            "success": False,
            "message": "Invalid editor ID."
        }), 400

    # The new system intentionally performs
    # a complete replacement instead of
    # an indentation-only correction.

    result = fix_full_code(
        editor_id
    )

    return jsonify(result)


# ============================================================
# GET TEMPLATE
# ============================================================

@app.route(
    "/template",
    methods=["GET"]
)
def get_template():

    editor_id = request.args.get(
        "editor_id"
    )

    if editor_id:

        if editor_id not in REGISTERED_CODES:

            return jsonify({
                "success": False,
                "message": "Invalid editor ID."
            }), 400

        return jsonify({
            "success": True,
            "editor_id": editor_id,
            "template_code": REGISTERED_CODES[
                editor_id
            ]
        })

    # Return all five templates
    return jsonify({
        "success": True,
        "templates": REGISTERED_CODES
    })


# ============================================================
# GET ALL REGISTERED CODES
# ============================================================

@app.route(
    "/registered-codes",
    methods=["GET"]
)
def registered_codes():

    return jsonify({
        "success": True,
        "codes": REGISTERED_CODES
    })


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            __import__("os").environ.get(
                "PORT",
                8000
            )
        )
    )
