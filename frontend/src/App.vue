<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
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
const location = ref('北京');
const messages = ref<Message[]>([
  { role: 'assistant', content: '你好！我是你的 AI 旅游助手。你可以问我关于北京的**推荐美食**、**住宿**、**游玩路线**，或者让我教你如何用 **Pocket 3** 拍出大片！' }
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
      body: JSON.stringify({ query: userQuery, location: location.value })
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

const setQuickQuery = (text: string) => {
  query.value = text;
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
        <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role]">
          <div class="avatar">
            <Sparkles v-if="msg.role === 'assistant'" :size="20" />
            <div v-else class="user-avatar">ME</div>
          </div>
          <div class="message-content glass" v-html="marked(msg.content)"></div>
        </div>
        <div v-if="isLoading && messages[messages.length-1].content === ''" class="message-wrapper assistant">
          <div class="avatar spinning"><Loader2 :size="20" /></div>
          <div class="message-content glass">AI 正在思考中...</div>
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
.footer { margin-top: auto; font-size: 12px; color: var(--text-secondary); text-align: center; }
</style>
