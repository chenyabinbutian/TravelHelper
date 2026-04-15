<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { marked } from 'marked';
import { 
  Send, 
  MapPin, 
  Camera, 
  Utensils, 
  Palmtree, 
  Navigation,
  Sparkles,
  Loader2
} from 'lucide-vue-next';

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
  
  // 先加入一个空的 AI 消息对象，用于后续追加流
  const assistantMsgIndex = messages.value.push({ role: 'assistant', content: '' }) - 1;
  
  await scrollToBottom();

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: userQuery, 
        location: location.value,
        history: messages.value.slice(0, -2) // 仅发送“之前”的对话，排除当前这一轮的提问和空回复
      })
    });

    if (!response.body) throw new Error('No body');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      // 处理 SSE 格式 (data: {...}\n\n)
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          if (dataStr === '[DONE]') break;
          try {
            const data = JSON.parse(dataStr);
            messages.value[assistantMsgIndex].content += data.content;
            await scrollToBottom();
          } catch (e) {
            console.error("JSON Parse Error", e);
          }
        }
      }
    }
  } catch (error) {
    messages.value[assistantMsgIndex].content = '抱歉，连接服务器失败。请确保后端 API 已启动且 Key 正确。';
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
};

const renderContent = (content: string) => {
  if (!content) return '';
  
  // 1. 先进行标准 Markdown 渲染 (表格、图片)
  // 将旧的不稳定 Unsplash 链接替换为更稳健的关键词获取方式
  let html = marked(content);

  // 2. 将 [MAP_LOCATION: 名称 | 地址 | 搜索词] 解析为动态搜索地图
  // 我们使用 OpenStreetMap 或简单的 Google Map 搜索链接模拟
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
    <aside class="sidebar glass">
      <div class="brand">
        <Sparkles class="brand-icon" />
        <h1>TravelHelper AI</h1>
      </div>
      <div class="location-picker">
        <MapPin :size="18" />
        <input v-model="location" placeholder="当前城市..." />
      </div>
      <nav class="quick-actions">
        <button @click="setQuickQuery('推荐一些地道美食')" class="action-btn">
          <Utensils :size="18" /> <span>美食推荐</span>
        </button>
        <button @click="setQuickQuery('帮我规划一条游玩路线')" class="action-btn">
          <Navigation :size="18" /> <span>旅游路线</span>
        </button>
        <button @click="setQuickQuery('Pocket 3 拍摄参数设置')" class="action-btn active">
          <Camera :size="18" /> <span>摄影参数</span>
        </button>
        <button @click="setQuickQuery('附近的高评分住宿')" class="action-btn">
          <Palmtree :size="18" /> <span>特色住宿</span>
        </button>
      </nav>
      <div class="footer"><p>Interview Demo v0.1</p></div>
    </aside>

    <main class="chat-area">
      <div class="messages-container" ref="chatContainer">
        <div v-for="(msg, index) in messages" :key="index" 
             :class="['message-wrapper', msg.role]">
          <div class="avatar">
            <Sparkles v-if="msg.role === 'assistant'" :size="20" />
            <div v-else class="user-avatar">ME</div>
          </div>
          <!-- 如果消息内容为空且正在加载，显示加载状态 -->
          <div v-if="msg.role === 'assistant' && msg.content === '' && isLoading" class="message-content glass">
            <div class="loading-state">
              <Loader2 :size="18" class="spinning" />
              <span>AI 正在思考中...</span>
            </div>
          </div>
          <!-- 渲染内容 -->
          <div v-else class="message-content glass">
            <div class="markdown-body" v-html="renderContent(msg.content)"></div>
          </div>
        </div>
      </div>

      <div class="input-section">
        <div class="input-wrapper glass">
          <input v-model="query" @keyup.enter="sendMessage" placeholder="问问 AI 你的旅游计划..." />
          <button @click="sendMessage" :disabled="isLoading" class="send-btn">
            <Send v-if="!isLoading" :size="20" />
            <Loader2 v-else class="spinning" :size="20" />
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* 保持之前的样式不变 */
.app-container { display: flex; width: 100vw; height: 100vh; padding: 20px; gap: 20px; }
.sidebar { width: 280px; padding: 24px; display: flex; flex-direction: column; gap: 32px; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-icon { color: var(--accent-color); }
.brand h1 { font-size: 1.25rem; font-weight: 700; }
.location-picker { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: rgba(0, 0, 0, 0.2); border-radius: 12px; }
.location-picker input { background: transparent; border: none; color: white; outline: none; width: 100%; }
.quick-actions { display: flex; flex-direction: column; gap: 12px; }
.action-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: transparent; border: none; border-radius: 12px; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; text-align: left; width: 100%; }
.action-btn:hover { background: rgba(255, 255, 255, 0.05); color: white; }
.action-btn.active { background: rgba(56, 189, 248, 0.1); color: var(--accent-color); }
.chat-area { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; }
.messages-container { flex: 1; overflow-y: auto; padding: 20px 40px; display: flex; flex-direction: column; gap: 24px; }
.message-wrapper { display: flex; gap: 16px; max-width: 85%; }
.message-wrapper.user { align-self: flex-end; flex-direction: row-reverse; }
.avatar { width: 40px; height: 40px; border-radius: 12px; background: var(--accent-color); display: flex; align-items: center; justify-content: center; color: #000; flex-shrink: 0; }
.user-avatar { font-weight: bold; font-size: 12px; }
.message-content { padding: 16px 20px; line-height: 1.6; font-size: 0.95rem; }
.user .message-content { background: var(--accent-color); color: #000; }
.input-section { padding: 20px 40px 40px; }
.input-wrapper { display: flex; align-items: center; padding: 8px 8px 8px 24px; gap: 12px; }
.input-wrapper input { flex: 1; background: transparent; border: none; color: white; font-size: 1rem; outline: none; }
.send-btn { width: 48px; height: 48px; border-radius: 12px; background: var(--accent-color); border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.spinning { animation: spin 2s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

/* Markdown 高级样式 */
:deep(.markdown-body table) { width: 100%; border-collapse: collapse; margin: 16px 0; background: rgba(255, 255, 255, 0.05); border-radius: 8px; overflow: hidden; }
:deep(.markdown-body th) { background: var(--accent-color); color: #000; padding: 12px; text-align: left; }
:deep(.markdown-body td) { padding: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
:deep(.markdown-body img) { max-width: 100%; border-radius: 12px; margin: 12px 0; border: 2px solid var(--border-color); }

/* 地图预览卡片 */
.map-card { margin: 16px 0; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); background: #1e293b; }
.map-header { padding: 10px 16px; border-bottom: 1px solid var(--border-color); font-weight: 600; }
.map-footer { padding: 8px 16px; font-size: 12px; color: var(--text-secondary); }

.footer { margin-top: auto; font-size: 12px; color: var(--text-secondary); text-align: center; }
</style>
