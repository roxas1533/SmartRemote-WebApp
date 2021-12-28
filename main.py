from flask import Flask, render_template, jsonify, request
import uuid
import json

from recordPlay import play, record

app = Flask(__name__)

remoteData = {}


@app.route("/")
def main():
    remoteDataHtml = []
    for id, data in remoteData.items():
        buttons = []
        for buttonId, button in data["button"].items():
            buttons.append(
                render_template(
                    "buttonComponent.html", uuid=buttonId, name=button["name"]
                )
            )
        remoteDataHtml.append(
            render_template(
                "newRemote.html", uuid=id, name=data["name"], buttons=buttons
            )
        )
    return render_template("main.html", remoteDataHtml=remoteDataHtml)


@app.route("/get-component", methods=["POST"])
def getComponent():
    newRegist = render_template("newRegist.html")
    deleteRemote = render_template("deleteRemote.html")
    newButton = render_template("newButton.html")
    recordWaiting = render_template("recordWaiting.html")
    editRemote = render_template("editRemote.html")
    buttonComponent = render_template("buttonComponent.html")
    return jsonify(
        {
            "newRegist": newRegist,
            "deleteRemote": deleteRemote,
            "newButton": newButton,
            "recordWaiting": recordWaiting,
            "editRemote": editRemote,
            "buttonComponent": buttonComponent,
        }
    )


@app.route("/new-register-remote", methods=["POST"])
def registerRemote():
    data = request.json["name"]
    uuidString = str(uuid.uuid4())
    remoteData[uuidString] = {"name": data, "button": {}}
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    return render_template("newRemote.html", uuid=uuidString, name=data)


@app.route("/delete-remote", methods=["POST"])
def delteRemote():
    data = request.json["id"]
    del remoteData[data]
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    return jsonify({"result": True})


@app.route("/delete-remote-button", methods=["POST"])
def delteRemoteButton():
    data = request.json["id"]
    uuid = request.json["buttonId"]
    del remoteData[data]["button"][uuid]
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    return jsonify({"result": True})


@app.route("/edit-remote", methods=["POST"])
def editRemote():
    data = request.json["id"]
    name = request.json["name"]
    remoteData[data]["name"] = name
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    return jsonify({"result": True, "name": name})


@app.route("/edit-button", methods=["POST"])
def editButton():
    data = request.json["id"]
    name = request.json["name"]
    uuid = request.json["buttonId"]
    remoteData[data]["button"][uuid]["name"] = name
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    return jsonify({"result": True, "name": name})


@app.route("/register-signal", methods=["POST"])
def registerSignal():
    uuidString = str(uuid.uuid4())
    result, signal = record([uuidString])
    return jsonify({"result": result, "id": uuidString, "signal": signal})


@app.route("/register-button", methods=["POST"])
def registerButton():
    data = request.json["name"]
    id = request.json["id"]
    signal = request.json["signal"]
    buttonId = request.json["buttonId"]
    remoteData[id]["button"][buttonId] = {"name": data, "signal": signal}
    with open("data.json", "w") as f:
        json.dump(remoteData, f, indent=4)
    buttonComponent = render_template("buttonComponent.html", uuid=buttonId, name=data)
    return jsonify({"result": True, "component": buttonComponent})


@app.route("/send-signal", methods=["POST"])
def sendSignal():
    id = request.json["id"]
    buttonId = request.json["buttonId"]
    code = remoteData[id]["button"][buttonId]["signal"]
    # 赤外線で送信するとなぜか2倍になって送信されるので半分にしておく
    play(list(map(lambda x: x // 2, code)))
    return jsonify({"result": True})


if __name__ == "__main__":
    with open("data.json") as f:
        remoteData = json.load(f)
    app.run(host="0.0.0.0", debug=True)
