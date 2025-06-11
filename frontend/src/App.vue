<template>
  <div id="app-container">
    <div class="card">
      <header class="card-header">
        <h1>VocaText</h1>
        <p>音视频转录工具</p>
      </header>

      <main class="card-body">
        <div class="upload-area">
          <input type="file" id="file-upload" @change="handleFileUpload" accept="audio/*,video/*" hidden />
          <label for="file-upload" class="upload-label">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            <span>{{ file ? file.name : '选择一个音频或视频文件' }}</span>
          </label>
          <button @click="submitFile" :disabled="!file || loading">
            <span v-if="!loading">开始转录</span>
            <div v-else class="spinner"></div>
          </button>
          <div class="options">
            <input type="checkbox" id="correct-checkbox" v-model="should_correct">
            <label for="correct-checkbox">对结果进行智能修正</label>
          </div>
        </div>

        <div v-if="error" class="result-box error-box">
          <strong>错误:</strong>
          <p>{{ error }}</p>
        </div>

        <div v-if="raw_transcription" class="result-box transcription-box">
          <strong>
            {{ corrected_transcription ? '修正后文本' : '转录结果' }}
          </strong>
          <pre>{{ corrected_transcription || raw_transcription }}</pre>
        </div>

        <div v-if="corrected_transcription" class="result-box raw-transcription-box">
          <strong>原始文本</strong>
          <pre>{{ raw_transcription }}</pre>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'App',
  setup() {
    const file = ref(null);
    const raw_transcription = ref('');
    const corrected_transcription = ref('');
    const error = ref('');
    const loading = ref(false);
    const should_correct = ref(true);

    const handleFileUpload = (event) => {
      file.value = event.target.files[0];
      raw_transcription.value = '';
      corrected_transcription.value = '';
      error.value = '';
    };

    const submitFile = async () => {
      if (!file.value) return;

      loading.value = true;
      error.value = '';
      raw_transcription.value = '';
      corrected_transcription.value = '';

      const formData = new FormData();
      formData.append('file', file.value);
      formData.append('correct', should_correct.value);

      try {
        const response = await fetch('/transcribe/', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.error || '转录失败');
        }
        
        raw_transcription.value = data.raw_text;
        if (data.is_corrected) {
          corrected_transcription.value = data.corrected_text;
        }

      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    return {
      file,
      raw_transcription,
      corrected_transcription,
      error,
      loading,
      should_correct,
      handleFileUpload,
      submitFile,
    };
  },
};
</script>

<style>
:root {
  --primary-color: #007aff;
  --background-color: #f4f4f9;
  --card-background: #ffffff;
  --text-color: #333;
  --subtle-text-color: #666;
  --border-color: #e0e0e0;
  --error-color: #ff3b30;
  --success-color: #34c759;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: var(--background-color);
  color: var(--text-color);
}

#app-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  padding: 40px 20px;
  box-sizing: border-box;
}

.card {
  width: 100%;
  max-width: 600px;
  background: var(--card-background);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-header {
  text-align: center;
  padding: 32px 24px;
  border-bottom: 1px solid var(--border-color);
}

.card-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  font-size: 16px;
  color: var(--subtle-text-color);
}

.card-body {
  padding: 24px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.options {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.options label {
  color: var(--subtle-text-color);
  font-size: 14px;
  cursor: pointer;
}

#correct-checkbox {
  cursor: pointer;
}

.upload-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
  text-align: center;
}

.upload-label:hover {
  background-color: #f9f9f9;
  border-color: var(--primary-color);
}

.upload-label span {
  color: var(--subtle-text-color);
  font-weight: 500;
}

button {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--primary-color);
  color: white;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  padding: 14px 24px;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  min-height: 48px;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button:not(:disabled):hover {
  background-color: #0056b3;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-box {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: #f9f9f9;
}

.result-box strong {
  display: block;
  margin-bottom: 8px;
}

.error-box {
  background-color: #fff0f0;
  border-color: var(--error-color);
  color: #a02020;
}

.transcription-box pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-family: "SF Mono", "Fira Code", "Fira Mono", "Roboto Mono", monospace;
  font-size: 14px;
  line-height: 1.6;
}

.raw-transcription-box {
  background-color: #f0f0f0;
  opacity: 0.8;
}

.raw-transcription-box pre {
  color: #555;
  font-size: 13px;
  line-height: 1.5;
}
</style>
