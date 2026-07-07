/**
 * Web Audio API helpers for push-to-talk recording and TTS playback.
 */

let currentAudio: HTMLAudioElement | null = null;
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

export function stopAudio(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
}

export async function playAudioBase64(base64: string): Promise<void> {
  stopAudio();
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: "audio/aiff" });
  const url = URL.createObjectURL(blob);
  currentAudio = new Audio(url);
  await currentAudio.play();
  currentAudio.onended = () => {
    URL.revokeObjectURL(url);
    currentAudio = null;
  };
}

export async function startRecording(): Promise<void> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  audioChunks = [];
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data);
  };
  mediaRecorder.start();
}

export async function stopRecording(): Promise<{ base64: string; mimeType: string }> {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) {
      reject(new Error("No active recording"));
      return;
    }
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      const buffer = await blob.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      mediaRecorder?.stream.getTracks().forEach((t) => t.stop());
      mediaRecorder = null;
      resolve({ base64: btoa(binary), mimeType: "audio/webm" });
    };
    mediaRecorder.stop();
  });
}

export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      resolve(dataUrl.split(",")[1]);
    };
    reader.readAsDataURL(blob);
  });
}
