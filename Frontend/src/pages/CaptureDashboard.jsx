import React, { useState, useRef } from "react";
import { FaMicrophone, FaStop } from "react-icons/fa";

export const CaptureDashboard = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [textInput, setTextInput] = useState("");
  const mediaRecorderRef = useRef(null);

  const StartRecording = async () => {
    try {
      setIsRecording(true);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      let chunks = [];

      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunks.push(ev.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(blob);
        setIsRecording(false);
        await uploadAudio(blob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
    } catch (err) {
      console.error("Mic error:", err);
      setIsRecording(false);
    }
  };

  const StopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      recorder.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const uploadAudio = async (blob) => {
    try {
      setIsUploading(true);

      const file = new File([blob], "recording.webm", {
        type: "audio/webm",
      });

      const formData = new FormData();
      formData.append("audio_file", file);

      const res = await fetch("http://localhost:8002/api/v1/process", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      console.log("Response:", data);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleTextSubmit = () => {
    console.log("Text:", textInput);
  };

  return (
    <div className="h-screen w-full bg-[#F5F7F8] flex flex-col items-center px-6 py-10">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl font-semibold text-gray-800">
          Release your thoughts to find clarity
        </h1>
        <p className="text-gray-500 mt-2">
          Speak or write — we’ll help you process it.
        </p>
      </div>

      {/* Cards */}
      <div className="flex gap-10 flex-wrap justify-center">
        {/* Voice Card */}
        <div className="bg-[#1E1E1E] text-white rounded-2xl p-6 w-80 flex flex-col items-center shadow-lg">
          <div
            className={`h-24 w-24 flex items-center justify-center rounded-full cursor-pointer transition 
            ${isRecording ? "bg-red-500 animate-pulse" : "bg-amber-400"}`}
            onClick={isRecording ? StopRecording : StartRecording}
          >
            {isRecording ? (
              <FaStop className="text-white text-2xl" />
            ) : (
              <FaMicrophone className="text-white text-2xl" />
            )}
          </div>

          <p className="font-semibold mt-4">Voice Capture</p>

          <p className="text-sm text-gray-300 text-center mt-2">
            Speak freely. We'll transcribe and organize your thoughts.
          </p>

          {isUploading && (
            <p className="text-xs text-amber-300 mt-3">
              Processing your audio...
            </p>
          )}
        </div>

        {/* Text Card */}
        <div className="bg-white rounded-2xl p-6 w-80 shadow-md flex flex-col">
          <p className="font-semibold text-gray-800 mb-3">Text Stream</p>

          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Write what's on your mind..."
            className="flex-1 resize-none p-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#78909C]"
          />

          <button
            onClick={handleTextSubmit}
            disabled={!textInput.trim()}
            className="mt-4 bg-[#78909C] text-white py-2 rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            Process
          </button>
        </div>
      </div>
    </div>
  );
};