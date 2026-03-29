import { useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002/api/v1";

export const CaptureDashboard = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [sessionId, setSessionId] = useState("");
  const [clarityScore, setClarityScore] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [clarificationAnswer, setClarificationAnswer] = useState("");
  const [breakdownCategories, setBreakdownCategories] = useState([]);
  const [breakdownIndex, setBreakdownIndex] = useState(0);
  const [categoryAnswer, setCategoryAnswer] = useState("");

  const currentCategory = useMemo(() => {
    if (!breakdownCategories.length) return "";
    return breakdownCategories[breakdownIndex] || "";
  }, [breakdownCategories, breakdownIndex]);

  const clearError = () => setError("");

  const parseError = async (res) => {
    try {
      const payload = await res.json();
      if (payload?.error?.message) return payload.error.message;
      if (payload?.detail) return String(payload.detail);
      return `Request failed (${res.status})`;
    } catch {
      return `Request failed (${res.status})`;
    }
  };

  const resetFlowForNewAudio = () => {
    setSessionId("");
    setClarityScore(null);
    setTasks([]);
    setFollowUpQuestion("");
    setClarificationAnswer("");
    setBreakdownCategories([]);
    setBreakdownIndex(0);
    setCategoryAnswer("");
  };

  const applySessionResponse = (data) => {
    setSessionId(data.session_id || "");
    setClarityScore(data.clarity_score ?? null);
    setTasks(Array.isArray(data.tasks) ? data.tasks : []);
    setFollowUpQuestion(data.follow_up_question || "");
    setBreakdownCategories(Array.isArray(data.suggested_breakdown_categories) ? data.suggested_breakdown_categories : []);
    setBreakdownIndex(0);
  };

  const startRecording = async () => {
    try {
      clearError();
      setIsRecording(true);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (ev) => {
        chunks.push(ev.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(blob);
        setIsRecording(false);
        uploadAudio(blob);
      };

      recorder.start();
      setMediaRecorder(recorder);
    } catch (err) {
      setIsRecording(false);
      setError(err?.message || "Could not access microphone");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  const uploadAudio = async (blobOrFile) => {
    if (!blobOrFile) return;

    setIsLoading(true);
    clearError();
    resetFlowForNewAudio();

    try {
      const file =
        blobOrFile instanceof File
          ? blobOrFile
          : new File([blobOrFile], "recording.webm", { type: "audio/webm" });

      const formData = new FormData();
      formData.append("audio_file", file);

      const res = await fetch(`${API_BASE_URL}/process`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(await parseError(res));
      }

      const data = await res.json();
      applySessionResponse(data);
    } catch (err) {
      setError(err?.message || "Failed to process audio");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (ev) => {
    const file = ev.target.files?.[0];
    if (!file) return;
    await uploadAudio(file);
    ev.target.value = "";
  };

  const submitClarification = async () => {
    if (!sessionId || !clarificationAnswer.trim()) return;
    setIsLoading(true);
    clearError();

    try {
      const res = await fetch(`${API_BASE_URL}/tasks/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          clarification_answer: clarificationAnswer.trim(),
        }),
      });

      if (!res.ok) {
        throw new Error(await parseError(res));
      }

      const data = await res.json();
      applySessionResponse(data);
      setClarificationAnswer("");
    } catch (err) {
      setError(err?.message || "Failed to refine tasks");
    } finally {
      setIsLoading(false);
    }
  };

  const submitCategoryBreakdown = async () => {
    if (!sessionId || !currentCategory || !categoryAnswer.trim()) return;
    setIsLoading(true);
    clearError();

    try {
      const res = await fetch(`${API_BASE_URL}/tasks/guided-breakdown`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          category: currentCategory,
          category_response: categoryAnswer.trim(),
        }),
      });

      if (!res.ok) {
        throw new Error(await parseError(res));
      }

      const data = await res.json();
      const newTasks = Array.isArray(data.tasks) ? data.tasks : [];
      setTasks((prev) => [...prev, ...newTasks]);
      setCategoryAnswer("");
      setBreakdownIndex((prev) => Math.min(prev + 1, breakdownCategories.length));
    } catch (err) {
      setError(err?.message || "Failed to process breakdown category");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSession = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    clearError();
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      const data = await res.json();
      applySessionResponse(data);
    } catch (err) {
      setError(err?.message || "Failed to refresh session");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTask = async (taskId, isCompleted) => {
    clearError();
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_completed: !isCompleted }),
      });
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      const updated = await res.json();
      setTasks((prev) => prev.map((task) => (task.id === taskId ? updated : task)));
    } catch (err) {
      setError(err?.message || "Failed to update task");
    }
  };

  const deleteTask = async (taskId) => {
    clearError();
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      setTasks((prev) => prev.filter((task) => task.id !== taskId));
    } catch (err) {
      setError(err?.message || "Failed to delete task");
    }
  };

  const breakdownActive = breakdownCategories.length > 0 && breakdownIndex < breakdownCategories.length;

  return (
    <>
      <div className="h-screen w-full bg-[#F5F7F8] flex flex-col">
        <div className="h-[25%]">
          <h1>Release your thoughts to find Clarity</h1>
          {isLoading && <p>Working...</p>}
          {sessionId && <p>Session: {sessionId}</p>}
          {clarityScore !== null && <p>Clarity score: {clarityScore}</p>}
          {error && <p className="text-red-600">{error}</p>}
        </div>

        <div className="flex flex-row gap-10 items-center justify-center">
          <div className="flex flex-col items-center justify-center h-72 w-72 bg-black rounded-xl gap-2 px-4">
            {!isRecording ? (
              <p onClick={startRecording} className="text-white cursor-pointer">
                MiC
              </p>
            ) : (
              <p className="text-white cursor-pointer" onClick={stopRecording}>
                Stop
              </p>
            )}
            <p className="text-white">Voice Capture</p>
            <input
              type="file"
              accept=".mp3,.m4a,.wav,.webm,.ogg,audio/*"
              onChange={handleFileUpload}
              className="text-white text-xs w-full"
            />
            {audioBlob && <p className="text-white text-xs">Audio ready</p>}
          </div>

          <div className="flex flex-col items-start justify-start h-72 w-72 bg-black rounded-xl p-3 overflow-y-auto gap-2">
            {!followUpQuestion && !breakdownActive && tasks.length === 0 && (
              <>
                <p className="text-white">MiC</p>
                <p className="text-white">Voice Capture</p>
              </>
            )}

            {followUpQuestion && (
              <>
                <p className="text-white text-sm">Clarification</p>
                <p className="text-white text-xs">{followUpQuestion}</p>
                <textarea
                  className="w-full bg-white text-black text-xs rounded p-1"
                  value={clarificationAnswer}
                  onChange={(ev) => setClarificationAnswer(ev.target.value)}
                  placeholder="Type clarification answer..."
                />
                <button
                  className="bg-gray-200 text-black text-xs px-2 py-1 rounded"
                  onClick={submitClarification}
                  disabled={isLoading || !clarificationAnswer.trim()}
                >
                  Submit clarification
                </button>
              </>
            )}

            {breakdownActive && (
              <>
                <p className="text-white text-sm">
                  Breakdown: {currentCategory} ({breakdownIndex + 1}/{breakdownCategories.length})
                </p>
                <textarea
                  className="w-full bg-white text-black text-xs rounded p-1"
                  value={categoryAnswer}
                  onChange={(ev) => setCategoryAnswer(ev.target.value)}
                  placeholder={`What's going on with ${currentCategory}?`}
                />
                <button
                  className="bg-gray-200 text-black text-xs px-2 py-1 rounded"
                  onClick={submitCategoryBreakdown}
                  disabled={isLoading || !categoryAnswer.trim()}
                >
                  Submit category
                </button>
                <button
                  className="bg-gray-200 text-black text-xs px-2 py-1 rounded"
                  onClick={refreshSession}
                  disabled={isLoading}
                >
                  Refresh session
                </button>
              </>
            )}

            {tasks.length > 0 && (
              <>
                <p className="text-white text-sm">Tasks ({tasks.length})</p>
                {tasks.map((task) => (
                  <div key={task.id} className="w-full bg-white rounded p-1 text-xs flex flex-col gap-1">
                    <p className={task.is_completed ? "line-through" : ""}>{task.text}</p>
                    <p className="text-[10px] text-gray-600">
                      {task.priority || "medium"}
                      {task.estimated_duration_minutes ? ` • ${task.estimated_duration_minutes} min` : ""}
                    </p>
                    <div className="flex gap-1">
                      <button
                        className="bg-gray-200 px-2 py-1 rounded"
                        onClick={() => toggleTask(task.id, task.is_completed)}
                      >
                        {task.is_completed ? "Undo" : "Done"}
                      </button>
                      <button
                        className="bg-red-200 px-2 py-1 rounded"
                        onClick={() => deleteTask(task.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
