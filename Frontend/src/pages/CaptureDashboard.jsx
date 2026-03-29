import React, { useState } from 'react'

export const CaptureDashboard =  () => {

    const [isRecording, setIsRecording] = useState(false)
    const [audioBlob, setAudioBlob] = useState(null)
    const [mediaRecorder, setMediaRecorder] = useState(null);

    const StartRecording = async () => {
        setIsRecording(true)
        const stream = await navigator.mediaDevices.getUserMedia({audio:true})
        console.log(stream)
        const recorder = new MediaRecorder(stream)
        console.log(recorder)



        let chunks = []

        recorder.ondataavailable = (ev)=>{
            chunks.push(ev.data)

        }

        recorder.onstop = () => {
            const blob = new Blob(chunks, {type: "audio/webm"})
            setAudioBlob(blob)
            setIsRecording(false)
            uploadAudio(blob)
        }

        recorder.start();
        setMediaRecorder(recorder);

    }

    const StopRecording =  () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive')
        {
            mediaRecorder.stop()
            mediaRecorder.stream.getTracks().forEach((track)=>track.stop())
            setIsRecording(false)
            console.log("Recording stopped")
        }
    }

const uploadAudio = async (blob) => {
    if (blob) {
        const file = new File([blob], "recording.webm", { type: "audio/webm" });

        const formData = new FormData();
        formData.append("audio_file", file);  // 👈 MUST match backend param name

        const res = await fetch("http://localhost:8002/api/v1/process", {
            method: "POST",
            body: formData, // 👈 NOT raw file
        });

        const data = await res.json();
        console.log(data);
    }
};


  return (
<>
    <div className='h-screen w-full bg-[#F5F7F8] flex flex-col'>

        <div className='h-[25%]'>
            <h1>Release your thoughts to find Clarity</h1>
        </div>

        <div className='flex flex-row gap-10 items-center justify-center'>
            <div className='flex flex-col items-center justify-center h-72 w-72 bg-black rounded-xl'>
                {
                    !isRecording ? <p onClick={()=>{
                    StartRecording()
                }}
                className='text-white'
                >MiC</p>: <p className='text-white' onClick={StopRecording}> Stop</p>
                }
                <p>Voice Capture</p>
            </div>

            <div className='flex flex-col items-center justify-center h-72 w-72 bg-black rounded-xl'>
                <p>MiC</p>
                <p>Voice Capture</p>
            </div>
        </div>

    </div>
</>
  )
}
