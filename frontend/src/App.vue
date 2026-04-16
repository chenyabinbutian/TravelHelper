<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { Send, User, Bot, Sparkles, Mic, MicOff } from 'lucide-vue-next';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const query = ref('');
const location = ref('');
const messages = ref<Message[]>([
  { role: 'assistant', content: '✨ 你好呀！我是你的【全球视觉旅行助手】。\n\n无论你想去**冰岛**拍极光、去**巴黎**拍人文，还是想了解 **DJI Pocket 3** 在任何环境下的最佳参数，都能在这里找到答案。准备好跟我一起出发了吗？' }
]);
const isLoading = ref(false);
const isListening = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

// 语音识别初始化
const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
if (recognition) {
  recognition.lang = 'zh-CN';
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onresult = (event: any) => {
    const transcript = Array.from(event.results)
      .map((result: any) => result[0])
      .map((result: any) => result.transcript)
      .join('');
    query.value = transcript;
  };

  recognition.onend = () => {
    isListening.value = false;
  };

  recognition.onerror = () => {
    isListening.value = false;
  };
}

const toggleMic = () => {
  if (!recognition) return alert('当前浏览器不支持语音识别');
  if (isListening.value) {
    recognition.stop();
  } else {
    isListening.value = true;
    recognition.start();
  }
};

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
      const parts: string[] = displayName.split(',').map((p: string) => p.trim());
      let cityPart = parts.find((p: string) => p.endsWith('市') || p.includes('市')) || '';
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
  let html = marked.parse(content) as string;
  
  // 匹配 [MAP_LOCATION: 内容]
  html = html.replace(/\[MAP_LOCATION: (.*?)\]/g, (_match: string, fullContent: string) => {
    // 灵活解析：支持 "名称 | 地址 | 搜索词" 或 直接是 "坐标/名称"
    const parts = fullContent.split('|').map(p => p.trim());
    const name = parts[0] || '目的地';
    const addr = parts[1] || '点击查看详情';
    const search = parts[2] || parts[0]; // 如果没搜到搜索词，就用名字
    
    const amapUrl = `https://uri.amap.com/search?keyword=${encodeURIComponent(search)}&src=TravelHelper&guide=1`;
    
    return `<div class="map-card" onclick="window.open('${amapUrl}', '_blank')">
      <div class="map-header">
        <div class="map-title">📍 ${name}</div>
        <div class="map-action">点击导航 →</div>
      </div>
      <div class="map-body">
         <div class="map-addr">${addr}</div>
         <div class="map-hint">由高德地图提供位置支持</div>
      </div>
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
          <button @click="toggleMic" :class="['mic-btn', { listening: isListening }]">
            <Mic v-if="!isListening" :size="18" />
            <div v-else class="pulse-ring"></div>
            <MicOff v-if="isListening" :size="18" />
          </button>
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

/* 全局极简滚动条 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.05); border-radius: 10px; transition: background 0.3s; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 0, 0, 0.1); }

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

.map-card { 
  background: white; 
  border-radius: 16px; 
  overflow: hidden; 
  border: 1px solid #e2e8f0; 
  margin: 16px 0; 
  cursor: pointer; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.map-card:hover { 
  transform: translateY(-4px); 
  box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.1); 
  border-color: var(--primary);
}
.map-header { 
  padding: 14px 18px; 
  background: #f8fafc; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  border-bottom: 1px solid #f1f5f9;
}
.map-title { font-weight: 700; color: #1e293b; font-size: 14px; }
.map-action { font-size: 12px; color: var(--primary); font-weight: 600; }
.map-body { padding: 16px 18px; }
.map-addr { font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 8px; }
.map-hint { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 4px; }
.map-hint::before { content: ""; width: 6px; height: 6px; background: #10b981; border-radius: 50%; display: inline-block; }

/* 输入区 */
.input-area { padding: 20px; background: transparent; }
.input-container { background: white; border-radius: 30px; display: flex; padding: 8px 8px 8px 20px; align-items: center; gap: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
.input-container input { flex: 1; border: none; outline: none; font-size: 15px; color: #1e293b; background: transparent; }

/* 麦克风样式 */
.mic-btn { width: 32px; height: 32px; border-radius: 50%; border: none; background: #f1f5f9; color: #64748b; cursor: pointer; display: flex; align-items: center; justify-content: center; position: relative; transition: all 0.3s; }
.mic-btn.listening { background: #fee2e2; color: #ef4444; }
.pulse-ring { position: absolute; width: 100%; height: 100%; border-radius: 50%; border: 2px solid #ef4444; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 100% { transform: scale(1.8); opacity: 0; } }

.send-btn { width: 40px; height: 40px; border-radius: 50%; background: var(--primary); border: none; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }

.typing span { animation: blink 1.4s infinite both; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }
</style>
