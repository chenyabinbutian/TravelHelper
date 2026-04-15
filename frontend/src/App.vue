<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { Send, Loader2, Plane, MapPin, User, Bot } from 'lucide-vue-next';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const query = ref('');
const location = ref('');
const messages = ref<Message[]>([
  { role: 'assistant', content: '你好！我是你的【全球视觉旅行助手】。🌎\n\n无论你想去**冰岛**拍极光、去**巴黎**拍人文，还是想了解 **DJI Pocket 3** 在任何环境下的最佳参数，我都能为你提供专业的行程表格、住宿地图及摄影建议。' }
]);
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const sendMessage = async () => {
  if (!query.value.trim() || isLoading.value) return;

  const userQuery = query.value;
  messages.value.push({ role: 'user', content: userQuery });
  query.value = '';
  isLoading.value = true;
  
  const assistantMsgIndex = messages.value.push({ role: 'assistant', content: '' }) - 1;
  await scrollToBottom();

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: userQuery, 
        location: location.value,
        history: messages.value.slice(0, -2)
      })
    });

    if (!response.body) throw new Error('No body');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') break;
          try {
            const parsed = JSON.parse(data);
            messages.value[assistantMsgIndex].content += parsed.content;
            await scrollToBottom();
          } catch (e) { /* ignore parse errors */ }
        }
      }
    }
  } catch (error) {
    messages.value[assistantMsgIndex].content = '抱歉，服务出现了一点问题。请稍后再试。';
  } finally {
    isLoading.value = false;
  }
};

const renderContent = (content: string) => {
  if (!content) return '';
  let html = marked(content);
  html = html.replace(/\[MAP_LOCATION: (.*?) \| (.*?) \| (.*?)\]/g, (match, name, addr, search) => {
    const query = encodeURIComponent(`${name} ${location.value}`);
    return `<div class="map-card glass">
      <div class="map-header">📍 酒店位置: ${name}</div>
      <div class="map-placeholder">
        <iframe width="100%" height="200" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
          src="https://maps.google.com/maps?q=${query}&t=&z=13&ie=UTF8&iwloc=&output=embed">
        </iframe>
      </div>
      <div class="map-footer">${addr}</div>
    </div>`;
  });
  return html;
};
</script>

<template>
  <div class="app-container">
    <header class="top-nav glass">
      <div class="nav-content">
        <div class="brand">
          <Plane class="brand-icon" :size="24" />
          <span class="brand-name">TravelHelper AI</span>
        </div>
        <div class="location-picker-compact glass">
          <MapPin :size="16" />
          <input v-model="location" placeholder="当前城市..." />
        </div>
      </div>
    </header>

    <main class="chat-area">
      <div class="messages-container" ref="chatContainer">
        <div v-for="(msg, idx) in messages" :key="idx" 
             :class="['message-wrapper', msg.role]">
          <div class="avatar glass">
            <User v-if="msg.role === 'user'" :size="20" />
            <Bot v-else :size="20" />
          </div>
          <div v-if="msg.content === ''" class="loading-state">
            <Loader2 class="spinning" :size="20" />
            <span>AI 正在思考...</span>
          </div>
          <div v-else class="message-content glass">
            <div class="markdown-body" v-html="renderContent(msg.content)"></div>
          </div>
        </div>
      </div>

      <div class="input-section">
        <div class="input-wrapper glass">
          <input v-model="query" @keyup.enter="sendMessage" placeholder="问问 AI 你的全球旅游计划..." />
          <button @click="sendMessage" :disabled="isLoading" class="send-btn">
            <Send v-if="!isLoading" :size="20" />
            <Loader2 v-else class="spinning" :size="20" />
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style>
:root {
  --bg-color: #0f172a;
  --accent-color: #38bdf8;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --glass-bg: rgba(30, 41, 59, 0.7);
  --border-color: rgba(255, 255, 255, 0.1);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg-color); color: var(--text-primary); font-family: 'Inter', sans-serif; overflow: hidden; }

.glass { background: var(--glass-bg); backdrop-filter: blur(12px); border: 1px solid var(--border-color); border-radius: 16px; }

.app-container { display: flex; flex-direction: column; width: 100vw; height: 100vh; }

.top-nav { height: 70px; width: 100%; display: flex; align-items: center; padding: 0 24px; position: sticky; top: 0; z-index: 100; border-radius: 0; border-top: none; border-left: none; border-right: none; }
.nav-content { max-width: 1000px; margin: 0 auto; width: 100%; display: flex; justify-content: space-between; align-items: center; }

.brand { display: flex; align-items: center; gap: 10px; }
.brand-name { font-weight: 700; font-size: 1.1rem; }
.brand-icon { color: var(--accent-color); }

.location-picker-compact { display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 10px; width: 180px; }
.location-picker-compact input { background: transparent; border: none; color: white; outline: none; font-size: 13px; width: 100%; }

.chat-area { flex: 1; display: flex; flex-direction: column; background: radial-gradient(circle at top right, #1e293b, #0f172a); overflow: hidden; }

.messages-container { flex: 1; overflow-y: auto; padding: 30px 20px; display: flex; flex-direction: column; gap: 24px; max-width: 900px; margin: 0 auto; width: 100%; }

.message-wrapper { display: flex; gap: 14px; max-width: 90%; align-self: flex-start; }
.message-wrapper.user { align-self: flex-end; flex-direction: row-reverse; }

.avatar { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: var(--glass-bg); flex-shrink: 0; }
.user .avatar { background: var(--accent-color); color: #000; }

.message-content { padding: 14px 18px; line-height: 1.6; font-size: 0.95rem; }
.user .message-content { background: var(--accent-color); color: #000; }

.input-section { padding: 20px; width: 100%; max-width: 900px; margin: 0 auto; }
.input-wrapper { display: flex; align-items: center; padding: 6px 6px 6px 20px; gap: 12px; }
.input-wrapper input { flex: 1; background: transparent; border: none; color: white; font-size: 1rem; outline: none; }

.send-btn { width: 44px; height: 44px; border-radius: 12px; background: var(--accent-color); border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s; }
.send-btn:hover { transform: scale(1.05); }

.spinning { animation: spin 2s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Markdown & Maps */
:deep(.markdown-body table) { width: 100%; border-collapse: collapse; margin: 12px 0; background: rgba(255, 255, 255, 0.05); border-radius: 8px; overflow: hidden; font-size: 13px; }
:deep(.markdown-body th) { background: rgba(56, 189, 248, 0.2); color: var(--accent-color); padding: 10px; text-align: left; }
:deep(.markdown-body td) { padding: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
:deep(.markdown-body img) { max-width: 100%; border-radius: 12px; margin: 10px 0; }

.map-card { margin: 12px 0; border-radius: 12px; overflow: hidden; background: #1e293b; }
.map-header { padding: 8px 14px; border-bottom: 1px solid var(--border-color); font-size: 13px; }
.map-footer { padding: 6px 14px; font-size: 11px; color: var(--text-secondary); }

/* Mobile Adaption */
@media (max-width: 640px) {
  .nav-content { padding: 0 4px; }
  .brand-name { display: none; }
  .location-picker-compact { width: 120px; }
  .messages-container { padding: 20px 12px; }
  .message-wrapper { max-width: 95%; }
  .input-section { padding: 12px; }
}
</style>
