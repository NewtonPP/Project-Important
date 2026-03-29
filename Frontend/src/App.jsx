import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const SCREENS = {
  RECORDING: "recording",
  PROCESSING: "processing",
  CLARIFICATION: "clarification",
  TASKS: "tasks",
  HISTORY: "history",
};

const defaultTaskImage =
  "https://lh3.googleusercontent.com/aida-public/AB6AXuBEvT3Z8wB7V0GJ5xAU-dTYiPS8zJ-eEGleFMDjKix1C8ifWC9KwqdWDNltVN5JbAdKYHxmfDlD5p37I3sjPtRIITf5qBQIZMtgMscYxWZ4vMMmXLexgGYYFU8WgzEkH8Uevj6vIP4dQfptxVR2C84zt4-O0Z1_Ae6ixtTLDCI9QXiexSG5f1iMuiHBQNjRtyMhMW7pNrb7hcBSBV8xaJpWlN8ZOfHab_WKopv5WsenVXGl0NEXgf8hpBqKlkHAKNPSXpEs2TC9O0s";

function App() {
  const fileInputRef = useRef(null);
  const recorderRef = useRef(null);
  const streamRef = useRef(null);

  const [screen, setScreen] = useState(SCREENS.RECORDING);
  const [error, setError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [clarityScore, setClarityScore] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [clarificationAnswer, setClarificationAnswer] = useState("");
  const [mode, setMode] = useState("refine");
  const [categories, setCategories] = useState([]);
  const [categoryIndex, setCategoryIndex] = useState(0);
  const [selectedQuickAnswer, setSelectedQuickAnswer] = useState("");
  const [processingProgress, setProcessingProgress] = useState(8);
  const [sessions, setSessions] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [sessionNames, setSessionNames] = useState({});

  const currentCategory = categories[categoryIndex] || "";
  const breakdownActive = mode === "breakdown" && categories.length > 0;

  const clarificationPrompt = useMemo(() => {
    if (breakdownActive) {
      return `Let's focus on ${currentCategory}. What's going on here?`;
    }
    return followUpQuestion || "Wait, I just want to be sure...";
  }, [breakdownActive, currentCategory, followUpQuestion]);

  const parseError = async (res) => {
    try {
      const payload = await res.json();
      return payload?.error?.message || payload?.detail || `Request failed (${res.status})`;
    } catch {
      return `Request failed (${res.status})`;
    }
  };

  useEffect(() => {
    if (screen !== SCREENS.PROCESSING) return undefined;

    setProcessingProgress(8);
    const timer = setInterval(() => {
      setProcessingProgress((prev) => {
        if (prev >= 92) return 92;
        if (prev < 45) return Math.min(prev + 4, 92);
        if (prev < 75) return Math.min(prev + 2, 92);
        return Math.min(prev + 1, 92);
      });
    }, 350);

    return () => clearInterval(timer);
  }, [screen]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("clarityvoice.sessionNames");
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        setSessionNames(parsed);
      }
    } catch {
      // Ignore localStorage parse errors.
    }
  }, []);

  const applySessionLikeResponse = (data) => {
    setSessionId(data.session_id || "");
    setClarityScore(data.clarity_score ?? null);
    setTasks(Array.isArray(data.tasks) ? data.tasks : []);
    setFollowUpQuestion(data.follow_up_question || "");

    const suggested = Array.isArray(data.suggested_breakdown_categories)
      ? data.suggested_breakdown_categories
      : [];
    setCategories(suggested);
    setCategoryIndex(0);

    if (!data.needs_clarification) {
      setMode("refine");
      setScreen(SCREENS.TASKS);
      return;
    }

    if (suggested.length > 0) {
      setMode("breakdown");
      setScreen(SCREENS.CLARIFICATION);
      return;
    }

    setMode("refine");
    setScreen(SCREENS.CLARIFICATION);
  };

  const processAudio = async (audioBlobOrFile) => {
    setError("");
    setProcessingProgress(8);
    setScreen(SCREENS.PROCESSING);

    try {
      const audioFile =
        audioBlobOrFile instanceof File
          ? audioBlobOrFile
          : new File([audioBlobOrFile], "recording.webm", { type: "audio/webm" });

      const formData = new FormData();
      formData.append("audio_file", audioFile);

      const res = await fetch(`${API_BASE_URL}/process`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(await parseError(res));
      }

      const data = await res.json();
      applySessionLikeResponse(data);
    } catch (err) {
      setError(err?.message || "Could not process audio.");
      setScreen(SCREENS.RECORDING);
    }
  };

  const startRecording = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (event) => chunks.push(event.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        await processAudio(blob);
      };

      recorderRef.current = recorder;
      streamRef.current = stream;
      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setError(err?.message || "Microphone access failed.");
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state === "inactive") return;
    recorderRef.current.stop();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
  };

  const onUploadClick = () => fileInputRef.current?.click();

  const onFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await processAudio(file);
    event.target.value = "";
  };

  const submitClarification = async () => {
    const answer = clarificationAnswer.trim() || selectedQuickAnswer.trim();
    if (!sessionId || !answer) return;
    setError("");
    setProcessingProgress(8);
    setScreen(SCREENS.PROCESSING);

    try {
      if (mode === "refine") {
        const res = await fetch(`${API_BASE_URL}/tasks/refine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            clarification_answer: answer,
          }),
        });
        if (!res.ok) {
          throw new Error(await parseError(res));
        }
        const data = await res.json();
        setClarificationAnswer("");
        setSelectedQuickAnswer("");
        applySessionLikeResponse(data);
        return;
      }

      const categoryToSend = currentCategory;
      const res = await fetch(`${API_BASE_URL}/tasks/guided-breakdown`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          category: categoryToSend,
          category_response: answer,
        }),
      });
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      const categoryData = await res.json();
      const extracted = Array.isArray(categoryData.tasks) ? categoryData.tasks : [];
      setTasks((prev) => [...prev, ...extracted]);
      setClarificationAnswer("");
      setSelectedQuickAnswer("");

      const nextIndex = categoryIndex + 1;
      if (nextIndex < categories.length) {
        setCategoryIndex(nextIndex);
        setScreen(SCREENS.CLARIFICATION);
        return;
      }

      const finalRes = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
      if (!finalRes.ok) {
        throw new Error(await parseError(finalRes));
      }
      const finalData = await finalRes.json();
      applySessionLikeResponse({ ...finalData, needs_clarification: false });
      setScreen(SCREENS.TASKS);
    } catch (err) {
      setError(err?.message || "Request failed.");
      setScreen(SCREENS.CLARIFICATION);
    }
  };

  const updateTask = async (taskId, isCompleted) => {
    setError("");
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
      setError(err?.message || "Could not update task.");
    }
  };

  const deleteTask = async (taskId) => {
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, { method: "DELETE" });
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      setTasks((prev) => prev.filter((task) => task.id !== taskId));
    } catch (err) {
      setError(err?.message || "Could not delete task.");
    }
  };

  const startOver = () => {
    setScreen(SCREENS.RECORDING);
    setError("");
    setSessionId("");
    setClarityScore(null);
    setTasks([]);
    setFollowUpQuestion("");
    setClarificationAnswer("");
    setSelectedQuickAnswer("");
    setMode("refine");
    setCategories([]);
    setCategoryIndex(0);
  };

  const saveSessionName = (targetSessionId, name) => {
    if (!targetSessionId) return;
    setSessionNames((prev) => {
      const trimmed = (name || "").trim();
      const next = { ...prev };
      if (trimmed) next[targetSessionId] = trimmed;
      else delete next[targetSessionId];
      localStorage.setItem("clarityvoice.sessionNames", JSON.stringify(next));
      return next;
    });
  };

  const openJournal = () => {
    if (screen === SCREENS.HISTORY) {
      setScreen(tasks.length > 0 ? SCREENS.TASKS : SCREENS.RECORDING);
    }
  };

  const openHistory = async () => {
    setError("");
    setHistoryError("");
    setHistoryLoading(true);
    setScreen(SCREENS.HISTORY);
    try {
      const res = await fetch(`${API_BASE_URL}/sessions?page=1&limit=20&order=desc`);
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      const data = await res.json();
      setSessions(Array.isArray(data.sessions) ? data.sessions : []);
    } catch (err) {
      setHistoryError(err?.message || "Could not load history.");
      setSessions([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadSessionFromHistory = async (historySessionId) => {
    setError("");
    setHistoryError("");
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${historySessionId}`);
      if (!res.ok) {
        throw new Error(await parseError(res));
      }
      const data = await res.json();
      applySessionLikeResponse({ ...data, needs_clarification: false });
      setScreen(SCREENS.TASKS);
    } catch (err) {
      setHistoryError(err?.message || "Could not open this journal.");
    }
  };

  return (
    <div className="dark min-h-screen custom-scrollbar">
      {screen === SCREENS.RECORDING && (
        <RecordingScreen
          error={error}
          isRecording={isRecording}
          onPrimaryAction={isRecording ? stopRecording : startRecording}
          onUploadClick={onUploadClick}
          onOpenJournal={openJournal}
          onOpenHistory={openHistory}
        />
      )}
      {screen === SCREENS.PROCESSING && (
        <ProcessingScreen
          progress={processingProgress}
          onOpenJournal={openJournal}
          onOpenHistory={openHistory}
        />
      )}
      {screen === SCREENS.CLARIFICATION && (
        <ClarificationScreen
          error={error}
          prompt={clarificationPrompt}
          answer={clarificationAnswer}
          setAnswer={setClarificationAnswer}
          selectedQuickAnswer={selectedQuickAnswer}
          setSelectedQuickAnswer={setSelectedQuickAnswer}
          stepText={breakdownActive ? `Step ${categoryIndex + 1} of ${categories.length}` : "Step 1 of 2"}
          mode={mode}
          category={currentCategory}
          onContinue={submitClarification}
          onOpenJournal={openJournal}
          onOpenHistory={openHistory}
        />
      )}
      {screen === SCREENS.TASKS && (
        <TaskListScreen
          error={error}
          tasks={tasks}
          clarityScore={clarityScore}
          onToggle={updateTask}
          onDelete={deleteTask}
          onStartOver={startOver}
          onOpenJournal={openJournal}
          onOpenHistory={openHistory}
          sessionId={sessionId}
          sessionName={sessionId ? sessionNames[sessionId] || "" : ""}
          onSessionNameChange={saveSessionName}
        />
      )}
      {screen === SCREENS.HISTORY && (
        <HistoryScreen
          loading={historyLoading}
          error={historyError}
          sessions={sessions}
          onOpenSession={loadSessionFromHistory}
          onStartNewRecording={startOver}
          onOpenJournal={openJournal}
          onOpenHistory={openHistory}
          sessionNames={sessionNames}
        />
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept=".mp3,.m4a,.wav,.webm,.ogg,audio/*"
        className="hidden"
        onChange={onFileChange}
      />
    </div>
  );
}

function TopBar({ activeTab = "journal", onOpenJournal, onOpenHistory, darkShell = false }) {
  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 ${
        darkShell
          ? "bg-[#131313] bg-gradient-to-b from-[#1B1C1C] to-transparent"
          : "bg-[#EFE9D5] bg-opacity-95 backdrop-blur-md dark:bg-[#131313]"
      }`}
    >
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-none">
        <div className="text-2xl font-serif italic text-[#2D2D2D] dark:text-[#EFE9D5]">ClarityVoice</div>
        <nav className="hidden md:flex items-center gap-8">
          <button
            className={`font-bold border-b-2 ${
              activeTab === "journal"
                ? "text-[#BC6C25] border-[#BC6C25]"
                : "text-[#2D2D2D] dark:text-[#EFE9D5] opacity-70 border-transparent"
            }`}
            onClick={onOpenJournal}
          >
            Journal
          </button>
          <button
            className={`font-bold border-b-2 ${
              activeTab === "history"
                ? "text-[#BC6C25] border-[#BC6C25]"
                : "text-[#2D2D2D] dark:text-[#EFE9D5] opacity-70 border-transparent"
            }`}
            onClick={onOpenHistory}
          >
            History
          </button>
        </nav>
        <div className="flex items-center gap-4">
          <button className="text-[#2D2D2D] dark:text-[#EFE9D5] opacity-70">
            <span className="material-symbols-outlined">account_circle</span>
          </button>
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="bg-[#1B1C1C] text-[#EFE9D5] w-full py-12 px-8 flex flex-col md:flex-row justify-between items-center gap-4 z-40">
      <div className="font-serif text-[#D4A373] text-lg italic">ClarityVoice</div>
      <div className="text-[#EFE9D5] opacity-60 font-sans text-sm tracking-wide leading-relaxed">
        Breathe easy-that&apos;s done.
      </div>
      <div className="flex items-center gap-8">
        <a className="text-[#EFE9D5] opacity-60 hover:text-[#BC6C25] transition-colors font-sans text-sm" href="#">
          Privacy
        </a>
        <a className="text-[#EFE9D5] opacity-60 hover:text-[#BC6C25] transition-colors font-sans text-sm" href="#">
          Terms
        </a>
        <a className="text-[#EFE9D5] opacity-60 hover:text-[#BC6C25] transition-colors font-sans text-sm" href="#">
          Support
        </a>
      </div>
    </footer>
  );
}

function RecordingScreen({ error, isRecording, onPrimaryAction, onUploadClick, onOpenJournal, onOpenHistory }) {
  return (
    <div className="bg-surface font-body text-on-surface selection:bg-primary-container selection:text-on-primary-container overflow-hidden min-h-screen">
      <div className="fixed inset-0 pointer-events-none noise-overlay z-50" />
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <svg className="w-full h-full" fill="none" viewBox="0 0 1440 900" xmlns="http://www.w3.org/2000/svg">
          <path
            className="signature-curve opacity-15"
            d="M-50,600 C200,550 400,750 700,650 C1000,550 1200,850 1500,800"
            stroke="currentColor"
            strokeLinecap="round"
            strokeWidth="1.5"
          />
          <path
            className="signature-curve opacity-15"
            d="M100,-100 C300,150 600,50 900,200 C1200,350 1400,100 1600,250"
            stroke="currentColor"
            strokeLinecap="round"
            strokeWidth="1.2"
          />
        </svg>
      </div>
      <TopBar activeTab="journal" onOpenJournal={onOpenJournal} onOpenHistory={onOpenHistory} />
      <main className="relative z-10 min-h-screen flex flex-col items-center justify-center p-8 bg-[#EFE9D5] dark:bg-transparent">
        <div className="max-w-2xl w-full flex flex-col items-center text-center">
          <div className="relative mb-16 group">
            <div className="absolute inset-0 bg-primary-container opacity-10 blur-3xl rounded-full scale-125" />
            <button
              className="breathing-circle relative z-10 w-64 h-64 md:w-80 md:h-80 bg-[#2D2D2D] dark:bg-surface-container-highest rounded-full flex items-center justify-center transition-transform hover:scale-[1.03] active:scale-95 ease-out duration-500 overflow-hidden"
              onClick={onPrimaryAction}
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent" />
              <div className="flex flex-col items-center gap-4">
                <span className="material-symbols-outlined text-primary-container text-7xl md:text-8xl">
                  {isRecording ? "stop_circle" : "mic"}
                </span>
                <div className="w-1.5 h-1.5 bg-[#BC6C25] rounded-full animate-pulse" />
              </div>
            </button>
          </div>
          <div className="space-y-4 mb-12">
            <h1 className="font-headline text-5xl md:text-6xl text-[#2D2D2D] dark:text-on-background tracking-tight">
              Ready when you are.
            </h1>
            <p className="font-body text-lg md:text-xl text-[#2D2D2D]/70 dark:text-on-surface-variant max-w-md mx-auto leading-relaxed">
              Just speak your mind. I&apos;ll take care of the rest.
            </p>
            {error ? <p className="text-sm text-red-300">{error}</p> : null}
          </div>
          <button
            className="bg-primary-container text-on-primary-container px-10 py-5 rounded-3xl font-body font-semibold text-lg shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 active:scale-95 flex items-center gap-3 mb-10"
            onClick={onPrimaryAction}
          >
            {isRecording ? "Tap to Stop Recording" : "Tap to Start Recording"}
          </button>
          <div className="flex flex-col items-center gap-6">
            <div className="h-[1px] w-24 bg-[#BC6C25]/20" />
            <button
              className="group flex items-center gap-3 font-body text-sm text-[#2D2D2D]/60 dark:text-on-surface-variant hover:text-[#BC6C25] dark:hover:text-primary transition-colors py-2 px-4 rounded-xl border border-transparent hover:border-[#BC6C25]/10"
              onClick={onUploadClick}
            >
              <span className="material-symbols-outlined text-xl">attachment</span>
              <span>Upload Audio</span>
            </button>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function ProcessingScreen({ progress, onOpenJournal, onOpenHistory }) {
  const stageText =
    progress < 40
      ? "Transcribing your audio"
      : progress < 75
        ? "Extracting actionable tasks"
        : "Analyzing nuances and tone";

  return (
    <div className="bg-background text-on-background font-body min-h-screen flex flex-col relative overflow-hidden">
      <div className="fixed inset-0 noise-overlay z-50" />
      <TopBar activeTab="journal" onOpenJournal={onOpenJournal} onOpenHistory={onOpenHistory} />
      <main className="flex-grow flex items-center justify-center px-6 pt-20 pb-12 relative">
        <div className="w-full max-w-2xl bg-surface-container-low rounded-2xl p-12 md:p-20 relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -mr-32 -mt-32 blur-3xl" />
          <div className="relative z-10 flex flex-col items-center text-center">
            <div className="mb-16 w-full flex justify-center items-center h-24">
              <svg className="w-full max-w-sm opacity-60" viewBox="0 0 200 40">
                <path
                  className="signature-curve"
                  d="M0 20 Q 25 5, 50 20 T 100 20 T 150 20 T 200 20"
                  fill="none"
                  stroke="#D4A373"
                  strokeLinecap="round"
                  strokeWidth="2"
                />
                <path
                  className="opacity-40"
                  d="M0 20 Q 25 35, 50 20 T 100 20 T 150 20 T 200 20"
                  fill="none"
                  stroke="#BC6C25"
                  strokeDasharray="4 4"
                  strokeLinecap="round"
                  strokeWidth="1"
                />
              </svg>
            </div>
            <h1 className="font-headline text-4xl md:text-5xl text-on-background mb-6 tracking-tight leading-tight">
              I&apos;m untangling your thoughts...
            </h1>
            <p className="font-body text-lg text-on-surface-variant mb-12 max-w-md mx-auto leading-relaxed">
              This won&apos;t take long. Take a deep breath.
            </p>
            <div className="w-full max-w-md space-y-4">
              <div className="relative h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-primary-container rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between items-center text-sm font-label uppercase tracking-widest text-on-surface-variant/60">
                <span>Clarity Meter</span>
                <span>{progress}% Complete</span>
              </div>
            </div>
            <div className="mt-16 flex items-center gap-3 px-6 py-3 bg-surface-container-highest rounded-full border border-outline-variant/10">
              <span className="material-symbols-outlined text-primary text-xl">graphic_eq</span>
              <span className="text-sm font-label font-medium text-on-surface-variant">{stageText}</span>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function ClarificationScreen({
  error,
  prompt,
  answer,
  setAnswer,
  selectedQuickAnswer,
  setSelectedQuickAnswer,
  stepText,
  mode,
  category,
  onContinue,
  onOpenJournal,
  onOpenHistory,
}) {
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    setSpeechSupported(true);
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (!transcript) return;
      setAnswer((prev) => `${prev} ${transcript}`.trim());
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognitionRef.current = recognition;
  }, [setAnswer]);

  const toggleVoiceInput = () => {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setVoiceMessage("Voice input is not supported in this browser. Please use Chrome/Edge.");
      return;
    }
    setVoiceMessage("");
    if (listening) {
      recognition.stop();
      setListening(false);
      return;
    }
    recognition.start();
    setListening(true);
  };

  const quickChoices =
    mode === "breakdown"
      ? [category || "Category", "Skip This", "Something Else"]
      : ["Work", "Personal Studio", "Something Else"];

  return (
    <div className="bg-background text-on-background font-body custom-scrollbar min-h-screen">
      <div className="fixed inset-0 noise-overlay z-50" />
      <TopBar activeTab="journal" onOpenJournal={onOpenJournal} onOpenHistory={onOpenHistory} />
      <main className="min-h-screen pt-24 pb-32 flex flex-col items-center justify-center px-4 relative">
        <div className="mb-12 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#BC6C25]" />
          <div className="w-2 h-2 rounded-full bg-surface-container-highest opacity-30" />
          <span className="text-xs uppercase tracking-widest text-on-surface-variant font-label ml-2">{stepText}</span>
        </div>
        <section className="max-w-2xl w-full">
          <div className="relative p-1 bg-gradient-to-br from-surface-container-highest/20 to-transparent signature-curve">
            <div className="bg-tertiary/5 dark:bg-surface-container-low p-8 md:p-12 rounded-3xl shadow-2xl relative overflow-hidden backdrop-blur-sm border border-outline-variant/10">
              <div className="mb-8 flex flex-col items-center text-center">
                <h1 className="font-serif text-4xl md:text-5xl text-[#2D2D2D] dark:text-[#EFE9D5] mb-4 leading-tight">
                  Wait, I just want to be sure...
                </h1>
                <p className="text-lg text-on-surface-variant font-body max-w-md leading-relaxed">
                  {prompt}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
                {quickChoices.map((choice, idx) => (
                  <button
                    key={choice}
                    className={`group flex flex-col items-center p-6 bg-surface-container text-on-surface rounded-2xl border transition-all duration-500 active:scale-95 ${
                      selectedQuickAnswer === choice
                        ? "border-primary-container/50 bg-surface-container-high"
                        : "border-transparent hover:border-primary-container/30 hover:bg-surface-container-high"
                    }`}
                    onClick={() => {
                      setSelectedQuickAnswer(choice);
                      if (choice === "Skip This") setAnswer("nothing here");
                      else setAnswer(choice);
                    }}
                  >
                    <div className="w-12 h-12 flex items-center justify-center rounded-full bg-primary-container/10 mb-3 text-primary-container group-hover:scale-110 transition-transform">
                      <span className="material-symbols-outlined text-3xl">
                        {idx === 0 ? "work" : idx === 1 ? "brush" : "more_horiz"}
                      </span>
                    </div>
                    <span className="font-label font-semibold text-sm">{choice}</span>
                  </button>
                ))}
              </div>
              <div className="relative group">
                <label className="sr-only" htmlFor="clarification-text">
                  Tell me more
                </label>
                <input
                  className="w-full bg-transparent border-b-2 border-outline-variant/30 py-4 px-2 focus:outline-none focus:border-tertiary transition-colors font-body text-on-surface placeholder:text-on-surface-variant/40 text-lg"
                  id="clarification-text"
                  placeholder="Tell me more if you'd like..."
                  type="text"
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                />
                <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-tertiary group-focus-within:w-full transition-all duration-700 ease-out" />
              </div>
              <div className="mt-12 flex justify-end">
                <div className="flex items-center gap-3">
                  <button
                    className={`px-6 py-4 rounded-3xl font-label font-bold flex items-center gap-2 transition-all shadow-lg ${
                      listening
                        ? "bg-[#BC6C25] text-white"
                        : "bg-surface-container-high text-on-surface"
                    }`}
                    onClick={toggleVoiceInput}
                    title={speechSupported ? "Use microphone for this answer" : "Voice not supported in this browser"}
                  >
                    <span className="material-symbols-outlined">{listening ? "mic_off" : "mic"}</span>
                    <span>{listening ? "Stop Voice" : "Voice Input"}</span>
                  </button>
                  <button
                    className="bg-primary-container text-on-primary-container px-8 py-4 rounded-3xl font-label font-bold flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-lg disabled:opacity-50"
                    onClick={onContinue}
                    disabled={!answer.trim()}
                  >
                    <span>Continue</span>
                    <span className="material-symbols-outlined">arrow_forward</span>
                  </button>
                </div>
              </div>
              {voiceMessage ? <p className="mt-3 text-xs text-amber-300">{voiceMessage}</p> : null}
              {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}
              <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-tertiary opacity-5 signature-curve pointer-events-none" />
            </div>
          </div>
          <p className="mt-8 text-center text-on-surface-variant/60 font-body text-sm italic">
            Accuracy is the foundation of clarity.
          </p>
        </section>
      </main>
      <Footer />
    </div>
  );
}

function TaskListScreen({
  error,
  tasks,
  clarityScore,
  onToggle,
  onDelete,
  onStartOver,
  onOpenJournal,
  onOpenHistory,
  sessionId,
  sessionName,
  onSessionNameChange,
}) {
  const task1 = tasks[0];
  const task2 = tasks[1];
  const task3 = tasks[2];
  const task4 = tasks[3];
  const task5 = tasks[4];

  const priorityLabel = (item) =>
    item?.priority ? `Priority: ${String(item.priority).charAt(0).toUpperCase()}${String(item.priority).slice(1)}` : "Priority: Med";
  const durationLabel = (item) =>
    item?.estimated_duration_minutes ? `${item.estimated_duration_minutes} mins` : "20 mins";

  return (
    <div className="bg-surface text-on-surface font-body selection:bg-primary-container selection:text-on-primary-container min-h-screen noise-subtle">
      <TopBar activeTab="journal" onOpenJournal={onOpenJournal} onOpenHistory={onOpenHistory} />
      <main className="pt-24 pb-20 min-h-screen bg-[#EFE9D5] journal-canvas">
        <div className="max-w-5xl mx-auto px-6 lg:px-12">
          <div className="mb-16 mt-8">
            <h1 className="font-headline text-5xl md:text-6xl text-[#2D2D2D] leading-tight mb-4 tracking-tight">
              Here&apos;s your clear path forward.
            </h1>
            <p className="text-[#2D2D2D] opacity-80 text-lg md:text-xl font-body flex items-center gap-2">
              <span className="material-symbols-outlined text-[#BC6C25]">temp_preferences_custom</span>
              You&apos;ve organized {tasks.length} tasks{clarityScore ? ` (clarity ${clarityScore}/10)` : ""}. One step at a time.
            </p>
            <div className="mt-4 flex flex-col md:flex-row md:items-center gap-3">
              <label className="text-sm text-[#2D2D2D]/70">Session name</label>
              <input
                className="bg-white/70 text-[#2D2D2D] border border-[#D4A373]/30 rounded-xl px-4 py-2 w-full md:w-[24rem]"
                placeholder="e.g., Math assignment + evening meeting"
                value={sessionName}
                onChange={(event) => onSessionNameChange(sessionId, event.target.value)}
              />
            </div>
            {error ? <p className="text-sm text-red-700 mt-3">{error}</p> : null}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
            {task1 ? (
              <div className="md:col-span-7 asymmetric-card bg-[#F1F4F2] p-8 shadow-sm">
              <div className="flex justify-between items-start mb-6">
                <div className="flex gap-3">
                  <span className="px-3 py-1 bg-primary-container text-on-primary-container text-xs font-bold rounded-full tracking-wide">
                    {priorityLabel(task1)}
                  </span>
                  <span className="px-3 py-1 bg-[#BC6C25] text-white text-xs font-bold rounded-full tracking-wide">
                    {durationLabel(task1)}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    className="w-8 h-8 rounded-lg border-2 border-[#D4A373] flex items-center justify-center"
                    onClick={() => onToggle(task1.id, task1.is_completed)}
                  >
                    <span className="material-symbols-outlined text-[#BC6C25] text-sm">check</span>
                  </button>
                </div>
              </div>
              <h3 className={`font-headline text-2xl text-[#2D2D2D] mb-4 ${task1.is_completed ? "strike-through opacity-50" : ""}`}>
                {task1.text}
              </h3>
              </div>
            ) : null}

            {task2 ? (
              <div className="md:col-span-5 asymmetric-card bg-[#F1F4F2] p-8 shadow-sm md:mt-12">
              <div className="flex justify-between items-start mb-6">
                <span className="px-3 py-1 bg-[#BC6C25] text-white text-xs font-bold rounded-full tracking-wide">
                  {durationLabel(task2)}
                </span>
                <button
                  className="w-8 h-8 rounded-lg border-2 border-[#D4A373] flex items-center justify-center"
                  onClick={() => onToggle(task2.id, task2.is_completed)}
                >
                  <span className="material-symbols-outlined text-[#BC6C25] text-sm">check</span>
                </button>
              </div>
              <h3 className={`font-headline text-xl text-[#2D2D2D] ${task2.is_completed ? "strike-through opacity-50" : ""}`}>{task2.text}</h3>
              </div>
            ) : null}

            {task3 ? (
              <div className="md:col-span-12 asymmetric-card bg-[#F1F4F2] p-8 shadow-sm flex flex-col md:flex-row md:items-center gap-6">
              <div className="flex-1">
                <div className="flex gap-3 mb-4">
                  <span className="px-3 py-1 bg-primary-container text-on-primary-container text-xs font-bold rounded-full tracking-wide">
                    {priorityLabel(task3)}
                  </span>
                  <span className="px-3 py-1 bg-[#BC6C25] text-white text-xs font-bold rounded-full tracking-wide">
                    {durationLabel(task3)}
                  </span>
                </div>
                <h3 className={`font-headline text-2xl text-[#2D2D2D] ${task3.is_completed ? "strike-through opacity-50" : ""}`}>{task3.text}</h3>
              </div>
              <button
                className="w-12 h-12 rounded-xl border-2 border-[#D4A373] flex items-center justify-center"
                onClick={() => onToggle(task3.id, task3.is_completed)}
              >
                <span className="material-symbols-outlined text-[#BC6C25]">check</span>
              </button>
              </div>
            ) : null}

            {task4 ? (
              <div className="md:col-span-6 asymmetric-card bg-[#F1F4F2] p-8 shadow-sm">
              <div className="flex justify-between items-start mb-6">
                <span className="px-3 py-1 bg-[#BC6C25] text-white text-xs font-bold rounded-full tracking-wide">
                  {durationLabel(task4)}
                </span>
                <button
                  className="w-8 h-8 rounded-lg border-2 border-[#D4A373] flex items-center justify-center"
                  onClick={() => onToggle(task4.id, task4.is_completed)}
                >
                  <span className="material-symbols-outlined text-[#BC6C25] text-sm">check</span>
                </button>
              </div>
              <h3 className={`font-headline text-xl text-[#2D2D2D] ${task4.is_completed ? "strike-through opacity-50" : ""}`}>{task4.text}</h3>
              </div>
            ) : null}

            {task5 ? (
              <div className="md:col-span-6 asymmetric-card overflow-hidden bg-primary-container shadow-sm p-0 flex flex-col md:mt-[-2rem]">
              <div className="p-8 pb-4">
                <div className="flex justify-between items-start mb-4">
                  <span className="px-3 py-1 bg-[#2D2D2D] text-[#EFE9D5] text-xs font-bold rounded-full tracking-wide">
                    {task5.priority ? priorityLabel(task5) : "Reflective Task"}
                  </span>
                </div>
                <h3 className={`font-headline text-2xl text-on-primary-container ${task5.is_completed ? "strike-through opacity-70" : ""}`}>
                  {task5.text}
                </h3>
              </div>
              <div className="mt-auto">
                <img className="w-full h-48 object-cover mix-blend-multiply opacity-60" src={defaultTaskImage} alt="studio texture" />
              </div>
              </div>
            ) : null}
          </div>
          {tasks.length === 0 ? (
            <div className="mt-8 asymmetric-card bg-[#F1F4F2] p-8 shadow-sm">
              <h3 className="font-headline text-2xl text-[#2D2D2D]">No tasks yet</h3>
              <p className="text-[#2D2D2D] opacity-70 mt-2">Try recording again and add more specific details.</p>
            </div>
          ) : null}
          <div className="h-24" />
        </div>
      </main>
      <Footer />
      <div className="fixed bottom-8 right-8 z-50">
        <button
          className="flex items-center gap-3 bg-primary-container text-on-primary-container px-6 py-4 rounded-2xl shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 group"
          onClick={onStartOver}
          title="Start new recording"
        >
          <span className="material-symbols-outlined text-2xl group-hover:rotate-12 transition-transform">mic</span>
          <span className="font-label font-bold uppercase tracking-widest text-sm">Start New Recording</span>
        </button>
      </div>
    </div>
  );
}

function HistoryScreen({
  loading,
  error,
  sessions,
  onOpenSession,
  onStartNewRecording,
  onOpenJournal,
  onOpenHistory,
  sessionNames,
}) {
  const formatSessionDate = (isoDate) => {
    if (!isoDate) return "Unknown";
    const date = new Date(isoDate);
    if (Number.isNaN(date.getTime())) return "Unknown";
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="bg-background text-on-background font-body min-h-screen">
      <div className="fixed inset-0 noise-overlay z-[100]" />
      <TopBar activeTab="history" onOpenJournal={onOpenJournal} onOpenHistory={onOpenHistory} darkShell />
      <main className="pt-28 pb-32 px-6 max-w-5xl mx-auto min-h-screen relative">
        <div className="absolute top-40 right-0 w-64 h-64 bg-primary/5 rounded-full blur-[100px] -z-10" />
        <div className="absolute bottom-20 left-0 w-80 h-80 bg-secondary/5 rounded-full blur-[120px] -z-10" />

        <header className="mb-12">
          <h1 className="font-headline text-4xl md:text-5xl lg:text-6xl text-on-surface font-light tracking-tight mb-4">
            Your growth story continues.
          </h1>
          <p className="text-on-surface-variant text-lg max-w-xl font-light leading-relaxed">
            Reflecting on your journey helps clarify the path ahead. Every recording is a step toward focus.
          </p>
        </header>

        <section className="mb-16">
          <div className="bg-surface-container-low p-8 md:p-10 rounded-tr-[3rem] rounded-bl-[3rem] rounded-tl-2xl rounded-br-2xl shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 signature-curve transform rotate-180" />
            <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-8">
              <div className="space-y-4">
                <span className="font-label text-xs uppercase tracking-[0.2em] text-primary font-bold">Weekly Focus</span>
                <h2 className="font-headline text-3xl text-on-surface">
                  {sessions.length === 0
                    ? "No journals yet"
                    : `${sessions.length} journal sessions captured`}
                </h2>
                <p className="text-on-surface-variant/80 max-w-md">
                  {sessions.length === 0
                    ? "Start your first recording to build your history."
                    : "You are building momentum. Revisit any session to continue where you left off."}
                </p>
              </div>
              <div className="flex-1 w-full max-w-md">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-label text-sm text-on-surface-variant font-medium">Progress</span>
                  <span className="font-label text-sm text-primary font-bold">
                    {sessions.length} total sessions
                  </span>
                </div>
                <div className="h-3 w-full bg-surface-container-highest rounded-full overflow-hidden p-[2px]">
                  <div
                    className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(212,163,115,0.4)] transition-all duration-1000 ease-out"
                    style={{ width: `${Math.min(100, sessions.length * 10)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
          <div className="md:col-span-12 flex justify-between items-center mb-2 px-2">
            <h3 className="font-headline text-2xl text-on-surface">Recent Sessions</h3>
          </div>

          {loading ? (
            <div className="md:col-span-12 bg-surface-container-low rounded-2xl p-6 text-on-surface-variant">
              Loading history...
            </div>
          ) : null}

          {error ? (
            <div className="md:col-span-12 bg-surface-container-low rounded-2xl p-6 text-red-300">
              {error}
            </div>
          ) : null}

          {!loading && !error && sessions.length === 0 ? (
            <div className="md:col-span-12 bg-surface-container-low rounded-2xl p-6 text-on-surface-variant">
              No past journals found yet.
            </div>
          ) : null}

          {!loading &&
            !error &&
            sessions.map((session, index) => {
              const spanClass = index === 0 ? "md:col-span-7" : index === 1 ? "md:col-span-5" : "md:col-span-6";
              const roundClass =
                index === 0
                  ? "rounded-tl-3xl rounded-br-3xl rounded-tr-lg rounded-bl-lg"
                  : "rounded-tr-3xl rounded-bl-3xl rounded-tl-lg rounded-br-lg";

              return (
                <button
                  key={session.session_id}
                  className={`${spanClass} text-left bg-surface-container-low hover:bg-surface-container transition-all duration-500 ${roundClass} p-6 group cursor-pointer border border-transparent hover:border-outline-variant/10`}
                  onClick={() => onOpenSession(session.session_id)}
                >
                  <div className="flex justify-between items-start mb-8">
                    <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                      <span className="material-symbols-outlined text-2xl">menu_book</span>
                    </div>
                    <span className="font-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                      {formatSessionDate(session.created_at)}
                    </span>
                  </div>
                  <h4 className="font-headline text-xl text-on-surface mb-2">
                    {sessionNames[session.session_id] || `Session ${index + 1}`}
                  </h4>
                  <p className="text-on-surface-variant text-sm mb-4">
                    Clarity score: {session.clarity_score ?? "-"} / 10
                  </p>
                  <div className="flex justify-between text-[10px] font-label uppercase tracking-tighter text-on-surface-variant">
                    <span>{session.task_count} tasks</span>
                    <span>{session.completed_task_count} completed</span>
                  </div>
                </button>
              );
            })}
        </section>
      </main>

      <button
        className="fixed bottom-8 right-8 z-50 flex items-center gap-3 bg-primary-container text-on-primary-container px-6 py-4 rounded-2xl shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 group"
        onClick={onStartNewRecording}
      >
        <span className="material-symbols-outlined text-2xl group-hover:rotate-12 transition-transform">mic</span>
        <span className="font-label font-bold uppercase tracking-widest text-sm">Start New Recording</span>
      </button>
    </div>
  );
}

export default App;
