let component;
const headers = {
    'Content-Type': 'application/json'
  };
window.addEventListener("DOMContentLoaded",async (e)=>{
    const remoteButton=document.querySelector(".register-new-remote");
    await fetch("/get-component",{method:"POST",headers}).then((res)=> res.json()).then((res)=> component=res);
    const remote=Array.from(document.getElementsByClassName("remote"));
    remote.forEach(element => {
        setRemoteEvent(element);
    });
    remoteButton.addEventListener("click",(e)=>{
        document.body.insertAdjacentHTML('beforeend', component["newRegist"]);
        const overlay=document.querySelector(".overlay");
        const send=document.querySelector(".send");
        setDeleterEvent(overlay);


        send.addEventListener("click",async (e)=>{
            const name=document.getElementById("name").value;
            await fetch("/new-register-remote",
            {
                method:"POST",
                headers,
                body: JSON.stringify({"name":name})
            }
            ).then((res)=> res.text()).then((res)=>{
                const remoteArea=document.querySelector(".remote-area");
                remoteArea.insertAdjacentHTML("beforeend",res);
                const addedRemote=remoteArea.lastElementChild;
                setRemoteEvent(addedRemote);
                overlay.remove();
            });
        })
    })
})

//リモコン
function setRemoteEvent(element){
    const id=element.getAttribute("data");
        //リモコン削除ボタン
        element.querySelector(".delete-remote-button").addEventListener("click",(e)=>{
            document.body.insertAdjacentHTML('beforeend', component["deleteRemote"]);
            const overlay=document.querySelector(".overlay");
            setDeleterEvent(overlay);
            overlay.querySelector(".remote-name").innerHTML=element.querySelector(".fs-3").textContent
            overlay.querySelector(".send").addEventListener("click",async (e)=>{
                await fetch("/delete-remote",
            {
                method:"POST",
                headers,
                body: JSON.stringify({id})
            }
            ).then((res)=> res.json()).then((res)=>{
                overlay.remove();
                element.remove();
            });
            })
        })
        //リモコン編集ボタン
        element.querySelector(".edit-remote-button").addEventListener("click",(e)=>{
            document.body.insertAdjacentHTML('beforeend', component["editRemote"]);
            const overlay=document.querySelector(".overlay");
            setDeleterEvent(overlay);
            const nameInput=overlay.querySelector("#name")
            remoteName=element.querySelector(".fs-3")
            nameInput.value = remoteName.textContent
            overlay.querySelector(".send").addEventListener("click",async (e)=>{
            await fetch("/edit-remote",
            {
                method:"POST",
                headers,
                body: JSON.stringify({id,"name":nameInput.value})
            }
            ).then((res)=> res.json()).then((res)=>{
                remoteName.innerHTML=res["name"]
                overlay.remove();
            });
            })
        })
        //ボタン追加ボタン
        element.querySelector(".new-button").addEventListener("click",(e)=>{
            addNewRemoteButton(element)
        })
        //登録ボタン
        const remoteButton=Array.from(element.getElementsByClassName("remote-button"));
        remoteButton.forEach(button => {
            setButton(button,id);
        })
}

function setDeleterEvent(overlay){
    const editor=document.querySelector(".editor");
    const deleters= Array.from(document.getElementsByClassName("deleter"));
    deleters.forEach(deleter => {
        deleter.addEventListener("click",(e)=>{
            overlay.remove();
        })
    });
    editor.addEventListener("click",(e)=>{
        e.stopPropagation();
    })
}

function addNewRemoteButton(element){
    document.body.insertAdjacentHTML('beforeend', component["newButton"]);
    const overlay=document.querySelector(".overlay");
    setDeleterEvent(overlay);
    let signal=[];
    let buttonId=0;
    const id=element.getAttribute("data");
    const send=document.querySelector(".send");
    //信号登録
    overlay.querySelector(".record").addEventListener("click",(e)=>{
        //待機中画面
        overlay.insertAdjacentHTML('beforeend', component["recordWaiting"]);
        const nextoverlay=overlay.querySelector(".overlay");
        nextoverlay.addEventListener("click",(e)=>{
            e.stopPropagation();
            nextoverlay.remove();
        })
        //記録
        fetch("/register-signal",
        {
            method:"POST",
            headers,
            body: JSON.stringify({id})
        }
        ).then((res)=> res.json()).then((res)=>{
            nextoverlay.remove();
            if(res["result"]){
                signal=res["signal"]
                buttonId=res["id"]
                const notRegister=overlay.querySelector(".not-register")
                notRegister.classList.add("d-none")
                notRegister.classList.remove("d-flex")
                const registered=overlay.querySelector(".registered")
                registered.classList.remove("d-none")
                registered.classList.add("d-flex")
                send.removeAttribute("disabled");
            }else{
                alert("タイムアウトしました");
            }
            
        });
    })
    //送信
    send.addEventListener("click",async (e)=>{
        const name=overlay.querySelector(".button-name").value;
        if(buttonId){
        await fetch("/register-button",
            {
                method:"POST",
                headers,
                body: JSON.stringify({id,name,buttonId,signal})
            }
            ).then((res)=> res.json()).then((res)=>{
                const remoteButtonArea=element.querySelector(".remote-button-area");
                remoteButtonArea.insertAdjacentHTML('beforeend', res["component"]);
                const addedButton=remoteButtonArea.lastElementChild;
                setButton(addedButton,id);
                overlay.remove();
            });
        }

    });

}

function setButton(button,id){
    const buttonId=button.getAttribute("data");
    //削除ボタン
    button.querySelector(".delete-remote-button").addEventListener("click",(e)=>{
        document.body.insertAdjacentHTML('beforeend', component["deleteRemote"]);
        const overlay=document.querySelector(".overlay");
        setDeleterEvent(overlay);
        overlay.querySelector(".remote-name").innerHTML=button.querySelector(".fs-3").textContent
        overlay.querySelector(".send").addEventListener("click",async (e)=>{
            await fetch("/delete-remote-button",
        {
            method:"POST",
            headers,
            body: JSON.stringify({id,buttonId})
        }
        ).then((res)=> res.json()).then((res)=>{
            overlay.remove();
            button.remove();
        });
        })
    })

    //編集ボタン
    button.querySelector(".edit-remote-button").addEventListener("click",(e)=>{
        document.body.insertAdjacentHTML('beforeend', component["editRemote"]);
        const overlay=document.querySelector(".overlay");
        setDeleterEvent(overlay);
        const nameInput=overlay.querySelector("#name")
        remoteName=button.querySelector(".fs-3")
        nameInput.value = remoteName.textContent
        overlay.querySelector(".send").addEventListener("click",async (e)=>{
        await fetch("/edit-button",
        {
            method:"POST",
            headers,
            body: JSON.stringify({id,buttonId,"name":nameInput.value})
        }
        ).then((res)=> res.json()).then((res)=>{
            remoteName.innerHTML=res["name"]
            overlay.remove();
        });
        })
    })
    //信号送信
    button.querySelector(".send-signal").addEventListener("click",(e)=>{
        fetch("/send-signal",
        {
            method:"POST",
            headers,
            body: JSON.stringify({id,buttonId})
        }
        )
    });
}