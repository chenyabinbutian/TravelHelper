<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { Send, Loader2, Plane, MapPin, User, Bot, Sparkles } from 'lucide-vue-next';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const query = ref('');
const location = ref('');
const messages = ref<Message[]>([
  { role: 'assistant', content: '✨ 你好呀！我是你的【全球视觉旅行助手】。\n\n无论你想去**冰岛**拍极光、去**巴黎**拍人文，还是想了解 **DJI Pocket 3** 的最佳参数，都能在这里找到答案。准备好跟我一起出发了吗？' }
]);
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' });
  }
};

const getUserLocation = async () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(async (position) => {
    try {
      const { latitude, longitude } = position.coords;
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10`);
      const data = await res.json();
      const displayName = data.display_name || '';
      const parts = displayName.split(',').map(p => p.trim());
      let cityPart = parts.find(p => p.endsWith('市') || p.includes('市')) || '';
      location.value = cityPart.replace(/市|省/g, ''); 
    } catch (e) {
      console.log('定位失败');
    }
  });
};

onMounted(() => {
  getUserLocation();
});

const sendMessage = async () => {
  if (!query.value.trim() || isLoading.value) return;

  const userQuery = query.value;
  messages.value.push({ role: 'user', content: userQuery });
  query.value = '';
  isLoading.value = true;
  
  const assistantMsgIndex = messages.value.push({ role: 'assistant', content: '' }) - 1;
  await scrollToBottom();

  try {
    const historyWithContext = [
      ...(location.value ? [{ role: 'user', content: `[系统同步：我在${location.value}市]` }, { role: 'assistant', content: '收到。' }] : []),
      ...messages.value.slice(0, -2)
    ];

    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: userQuery, location: location.value, history: historyWithContext })
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') break;
          try {
            messages.value[assistantMsgIndex].content += JSON.parse(data).content;
            await scrollToBottom();
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    messages.value[assistantMsgIndex].content = '哎呀，信号走丢了...';
  } finally {
    isLoading.value = false;
  }
};

const renderContent = (content: string) => {
  if (!content) return '';
  let html = marked(content);
  html = html.replace(/\[MAP_LOCATION: (.*?) \| (.*?) \| (.*?)\]/g, (match, name, addr) => {
    const q = encodeURIComponent(`${name} ${location.value}`);
    return `<div class="map-card">
      <div class="map-header">📍 目的地: ${name}</div>
      <iframe width="100%" height="180" frameborder="0" src="https://maps.google.com/maps?q=${q}&t=&z=14&ie=UTF8&iwloc=&output=embed"></iframe>
      <div class="map-footer">${addr}</div>
    </div>`;
  });
  return html;
};
</script>

<template>
  <div class="app-container">
    <div class="main-content">
      <header class="navbar">
        <div class="brand">
          <div class="logo-box"><Sparkles :size="18" fill="white" /></div>
          <span class="brand-text">TravelHelper</span>
        </div>
      </header>

      <main class="chat-area" ref="chatContainer">
        <div class="chat-inner">
          <div v-for="(msg, idx) in messages" :key="idx" :class="['msg-row', msg.role]">
            <div class="avatar-circle">
              <User v-if="msg.role === 'user'" :size="18" />
              <Bot v-else :size="18" />
            </div>
            <div class="bubble-container">
              <div v-if="msg.content === ''" class="typing">正在思考<span>.</span><span>.</span><span>.</span></div>
              <div v-else class="bubble" v-html="renderContent(msg.content)"></div>
            </div>
          </div>
        </div>
      </main>

      <footer class="input-area">
        <div class="input-container">
          <input v-model="query" @keyup.enter="sendMessage" placeholder="想去哪儿？问问我吧..." />
          <button @click="sendMessage" :disabled="isLoading" class="send-btn">
            <Send :size="18" />
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --primary: #10b981; /* 薄荷绿 */
  --bg-soft: #f1f5f9;
  --bubble-ai: #ffffff;
  --bubble-user: #10b981;
  --text-main: #334155;
}

* { box-sizing: border-box; font-family: 'Noto Sans SC', sans-serif; }
body { margin: 0; background: #f8fafc; color: var(--text-main); height: 100vh; overflow: hidden; }

.app-container { height: 100vh; display: flex; justify-content: center; background: radial-gradient(circle at top right, #f0fdf4, #f8fafc); }
.main-content { width: 100%; max-width: 800px; display: flex; flex-direction: column; background: transparent; position: relative; }

/* 导航栏 */
.navbar { height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid rgba(0,0,0,0.05); }
.brand { display: flex; align-items: center; gap: 8px; }
.logo-box { width: 32px; height: 32px; background: var(--primary); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
.brand-text { font-weight: 700; color: #1e293b; letter-spacing: -0.5px; }
.location-tag { display: flex; align-items: center; gap: 5px; background: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; color: #64748b; border: 1px solid #e2e8f0; }

/* 聊天区 */
.chat-area { flex: 1; overflow-y: auto; padding: 20px; scroll-behavior: smooth; }
.chat-inner { display: flex; flex-direction: column; gap: 20px; }

.msg-row { display: flex; gap: 12px; max-width: 85%; }
.msg-row.user { align-self: flex-end; flex-direction: row-reverse; }

.avatar-circle { width: 34px; height: 34px; border-radius: 50%; background: white; border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.user .avatar-circle { background: var(--primary); color: white; border: none; }

.bubble { padding: 12px 16px; border-radius: 20px; font-size: 14px; line-height: 1.6; box-shadow: 0 4px 15px rgba(0,0,0,0.03); word-break: break-all; }
.assistant .bubble { background: var(--bubble-ai); border-top-left-radius: 4px; border: 1px solid #f1f5f9; }
.user .bubble { background: var(--bubble-user); color: white; border-top-right-radius: 4px; }

/* 表格卡片化 - 核心解决拥挤问题 */
:deep(.markdown-body table) { border-collapse: collapse; margin: 10px 0; width: 100%; }
@media (max-width: 600px) {
  :deep(.markdown-body table) { border: 0; }
  :deep(.markdown-body thead) { display: none; }
  :deep(.markdown-body tr) { display: block; background: #f8fafc; border-radius: 12px; padding: 10px; margin-bottom: 10px; border: 1px solid #e2e8f0; }
  :deep(.markdown-body td) { display: flex; justify-content: space-between; padding: 6px 0; border: none; font-size: 13px; border-bottom: 1px dashed #e2e8f0; }
  :deep(.markdown-body td:last-child) { border-bottom: none; }
  :deep(.markdown-body td::before) { content: attr(data-label); font-weight: bold; color: var(--primary); margin-right: 15px; }
}
/* 消息气泡内的表格样式 - 核心修复 */
.bubble table { 
  width: 100%; 
  border-collapse: collapse; 
  margin: 12px 0; 
  border: 1px solid #e2e8f0; 
  border-radius: 8px; 
  overflow: hidden; 
  background: white;
  table-layout: fixed;
}
.bubble th { 
  background: #f0fdf4; 
  color: #059669; 
  font-weight: 700; 
  padding: 10px; 
  font-size: 13px; 
  border-bottom: 2px solid #10b981;
}
.bubble td { 
  padding: 12px; 
  border: 1px solid #f1f5f9; 
  font-size: 13px; 
  color: #475569; 
  vertical-align: middle; 
  word-wrap: break-word;
}
/* 第一列 - 标签化 */
.bubble td:nth-child(1) { 
  width: 90px; 
  background: #f8fafc; 
  font-weight: 700; 
  color: #059669; 
  text-align: center;
}
/* 列表项分割线 */
.bubble td ul { padding: 0; margin: 0; list-style: none; }
.bubble td li { 
  padding: 8px 0; 
  border-bottom: 1px dashed #e2e8f0; 
}
.bubble td li:last-child { border-bottom: none; }
.bubble td li::before { content: "•"; color: var(--primary); margin-right: 8px; font-weight: bold; }

.map-card { background: white; border-radius: 15px; overflow: hidden; border: 1px solid #e2e8f0; margin: 10px 0; }
.map-header { padding: 10px; font-weight: 700; font-size: 13px; background: #f8fafc; }
.map-footer { padding: 8px; font-size: 11px; color: #94a3b8; }

/* 输入区 */
.input-area { padding: 20px; background: transparent; }
.input-container { background: white; border-radius: 30px; display: flex; padding: 8px 8px 8px 20px; align-items: center; gap: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
.input-container input { flex: 1; border: none; outline: none; font-size: 15px; color: #1e293b; }
.send-btn { width: 40px; height: 40px; border-radius: 50%; background: var(--primary); border: none; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }

.typing span { animation: blink 1.4s infinite both; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
</style>
