<template>
  <div class="typing-animation">
    <div class="typing-dots">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TypingAnimation'
}
</script>

<style lang="scss" scoped>
.typing-animation {
  display: inline-flex;
  align-items: center;
  height: 16px;
}

.typing-dots {
  display: flex;
  gap: 2px;
}

.dot {
  width: 4px;
  height: 4px;
  background-color: var(--primary-500);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;

  &:nth-child(1) {
    animation-delay: 0s;
  }

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>

