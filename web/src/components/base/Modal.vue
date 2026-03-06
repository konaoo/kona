<script setup lang="ts">
/**
 * Modal - 模态框组件
 * 用于弹窗、对话框等
 */

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface ModalProps {
  /** 是否显示 */
  show: boolean
  /** 标题 */
  title?: string
  /** 宽度 */
  width?: string | number
  /** 是否显示关闭按钮 */
  closable?: boolean
  /** 点击遮罩是否关闭 */
  maskClosable?: boolean
  /** 是否显示底部 */
  footer?: boolean
  /** 是否居中 */
  centered?: boolean
  /** 是否全屏 */
  fullscreen?: boolean
  /** 销毁时是否移除 DOM */
  destroyOnClose?: boolean
  /** 键盘 ESC 关闭 */
  keyboard?: boolean
  /** 动画持续时间（毫秒） */
  duration?: number
}

const props = withDefaults(defineProps<ModalProps>(), {
  show: false,
  width: 520,
  closable: true,
  maskClosable: true,
  footer: true,
  centered: true,
  fullscreen: false,
  destroyOnClose: false,
  keyboard: true,
  duration: 300
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  close: []
  ok: []
  cancel: []
  afterOpen: []
  afterClose: []
}>()

const visible = ref(false)
const animating = ref(false)

const modalClass = computed(() => {
  return [
    'modal',
    {
      'modal-fullscreen': props.fullscreen,
      'modal-centered': props.centered
    }
  ]
})

const modalStyle = computed(() => {
  if (props.fullscreen) {
    return {}
  }

  const width = typeof props.width === 'number' ? `${props.width}px` : props.width
  return {
    width
  }
})

const maskClass = computed(() => {
  return [
    'modal-mask',
    {
      'modal-mask-visible': visible.value
    }
  ]
})

const handleMaskClick = () => {
  if (props.maskClosable) {
    close()
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (props.keyboard && e.key === 'Escape' && props.show) {
    close()
  }
}

const close = () => {
  emit('update:show', false)
  emit('close')
}

const handleOk = () => {
  emit('ok')
}

const handleCancel = () => {
  emit('cancel')
  close()
}

const openModal = async () => {
  visible.value = true
  animating.value = true

  // 锁定滚动
  document.body.style.overflow = 'hidden'

  await nextTick()
  setTimeout(() => {
    animating.value = false
  }, props.duration)

  emit('afterOpen')
}

const closeModal = async () => {
  animating.value = true

  setTimeout(() => {
    visible.value = false
    animating.value = false

    // 恢复滚动
    document.body.style.overflow = ''

    emit('afterClose')
  }, props.duration)
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    openModal()
  } else {
    closeModal()
  }
})

onMounted(() => {
  if (props.show) {
    openModal()
  }

  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)

  // 确保恢复滚动
  if (visible.value) {
    document.body.style.overflow = ''
  }
})
</script>

<template>
  <teleport to="body">
    <transition name="modal-fade">
      <div v-if="show || visible" :class="maskClass" @click="handleMaskClick">
        <transition name="modal-slide">
          <div
            v-if="show || visible || !destroyOnClose"
            ref="modalRef"
            :class="modalClass"
            :style="modalStyle"
            @click.stop
          >
            <div class="modal-header" v-if="title || $slots.header || closable">
              <slot name="header">
                <div class="modal-title">{{ title }}</div>
              </slot>
              <button
                v-if="closable"
                class="modal-close"
                @click="close"
                type="button"
              >
                ×
              </button>
            </div>

            <div class="modal-body">
              <slot />
            </div>

            <div class="modal-footer" v-if="footer || $slots.footer">
              <slot name="footer">
                <button class="btn btn-ghost" @click="handleCancel">
                  取消
                </button>
                <button class="btn btn-primary" @click="handleOk">
                  确定
                </button>
              </slot>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   MODAL COMPONENT - 模态框组件样式
   ═══════════════════════════════════════════════════════════════ */

.modal-mask {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.modal-mask-visible {
  opacity: 1;
}

/* ───────────────────────────────────────────────────────────────
   MODAL CONTENT - 模态框内容
   ─────────────────────────────────────────────────────────────── */

.modal {
  position: relative;
  background: var(--s2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  transform: scale(0.9);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-content-visible {
  transform: scale(1);
  opacity: 1;
}

.modal-centered {
  margin: auto;
}

.modal-fullscreen {
  width: 100vw !important;
  height: 100vh;
  max-width: none;
  max-height: none;
  border-radius: 0;
  margin: 0;
}

/* ───────────────────────────────────────────────────────────────
   MODAL HEADER - 头部
   ─────────────────────────────────────────────────────────────── */

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  line-height: 1.4;
}

.modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 24px;
  line-height: 1;
  color: var(--muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-default);
  flex-shrink: 0;
}

.modal-close:hover {
  color: var(--text);
  background: var(--s3);
}

/* ───────────────────────────────────────────────────────────────
   MODAL BODY - 内容区
   ─────────────────────────────────────────────────────────────── */

.modal-body {
  flex: 1;
  padding: var(--space-6);
  overflow: auto;
  color: var(--text);
  font-size: var(--font-size-base);
  line-height: 1.6;
}

/* ───────────────────────────────────────────────────────────────
   MODAL FOOTER - 底部
   ─────────────────────────────────────────────────────────────── */

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

/* ───────────────────────────────────────────────────────────────
   TRANSITIONS - 过渡动画
   ─────────────────────────────────────────────────────────────── */

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-slide-enter-active,
.modal-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-slide-enter-from,
.modal-slide-leave-to {
  transform: scale(0.9) translateY(-20px);
  opacity: 0;
}
</style>
