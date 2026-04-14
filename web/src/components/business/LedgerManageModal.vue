<script setup lang="ts">
import { ref, watch } from 'vue'
import { useLedgerScopeStore, type Ledger } from '@/stores/ledgerScope'
import Modal from '@/components/base/Modal.vue'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const ledgerStore = useLedgerScopeStore()

const newName = ref('')
const showCreateInput = ref(false)
const renamingId = ref<number | null>(null)
const renameValue = ref('')
const busy = ref(false)

watch(() => props.show, (v) => {
  if (v) {
    showCreateInput.value = false
    newName.value = ''
    renamingId.value = null
  }
})

function close() {
  emit('update:show', false)
}

async function handleCreate() {
  if (!newName.value.trim()) return
  busy.value = true
  const result = await ledgerStore.createLedger(newName.value)
  busy.value = false
  if (result.ok) {
    newName.value = ''
    showCreateInput.value = false
  } else {
    alert(result.message || '创建失败')
  }
}

function startRename(ledger: Ledger) {
  renamingId.value = ledger.id
  renameValue.value = ledger.name
}

async function handleRename(ledger: Ledger) {
  const name = renameValue.value.trim()
  if (!name || name === ledger.name) {
    renamingId.value = null
    return
  }
  busy.value = true
  const result = await ledgerStore.updateLedger(ledger.id, name)
  busy.value = false
  if (result.ok) {
    renamingId.value = null
  } else {
    alert(result.message || '重命名失败')
  }
}

async function handleDelete(ledger: Ledger) {
  if (ledgerStore.isDefault(ledger)) {
    alert('默认账本不能删除')
    return
  }
  if (!confirm(`确定删除"${ledger.name}"吗？`)) return
  busy.value = true
  const result = await ledgerStore.deleteLedger(ledger.id)
  busy.value = false
  if (!result.ok) {
    alert(result.message || '删除失败')
  }
}

async function handleMoveUp(index: number) {
  if (index <= 0) return
  const ids: number[] = ledgerStore.ledgers.map(l => l.id)
  const tmp = ids[index - 1]!
  ids[index - 1] = ids[index]!
  ids[index] = tmp
  busy.value = true
  await ledgerStore.reorderLedgers(ids)
  busy.value = false
}

async function handleMoveDown(index: number) {
  if (index >= ledgerStore.ledgers.length - 1) return
  const ids: number[] = ledgerStore.ledgers.map(l => l.id)
  const tmp = ids[index]!
  ids[index] = ids[index + 1]!
  ids[index + 1] = tmp
  busy.value = true
  await ledgerStore.reorderLedgers(ids)
  busy.value = false
}
</script>

<template>
  <Modal
    :show="show"
    title="管理账本"
    :width="480"
    :footer="false"
    @update:show="emit('update:show', $event)"
    @close="close"
  >
    <div class="ledger-manage">
      <!-- Ledger List -->
      <div class="ledger-list">
        <div
          v-for="(ledger, idx) in ledgerStore.ledgers"
          :key="ledger.id"
          class="ledger-item"
        >
          <div class="ledger-info">
            <template v-if="renamingId === ledger.id">
              <input
                v-model="renameValue"
                class="rename-input"
                autofocus
                @keyup.enter="handleRename(ledger)"
                @keyup.escape="renamingId = null"
                @blur="handleRename(ledger)"
              />
            </template>
            <template v-else>
              <span class="ledger-name">{{ ledger.name }}</span>
              <span v-if="ledgerStore.isDefault(ledger)" class="default-badge">默认</span>
            </template>
          </div>
          <div class="ledger-actions">
            <button
              class="act-btn"
              title="上移"
              :disabled="idx === 0 || busy"
              @click="handleMoveUp(idx)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </button>
            <button
              class="act-btn"
              title="下移"
              :disabled="idx === ledgerStore.ledgers.length - 1 || busy"
              @click="handleMoveDown(idx)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
            <button
              class="act-btn"
              title="重命名"
              :disabled="busy"
              @click="startRename(ledger)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
            <button
              class="act-btn danger"
              title="删除"
              :disabled="ledgerStore.isDefault(ledger) || busy"
              @click="handleDelete(ledger)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Create New -->
      <div class="create-section">
        <template v-if="showCreateInput">
          <div class="create-row">
            <input
              v-model="newName"
              class="create-input"
              placeholder="账本名称"
              autofocus
              @keyup.enter="handleCreate"
              @keyup.escape="showCreateInput = false"
            />
            <button class="create-confirm-btn" :disabled="!newName.trim() || busy" @click="handleCreate">
              创建
            </button>
            <button class="create-cancel-btn" @click="showCreateInput = false">
              取消
            </button>
          </div>
        </template>
        <template v-else>
          <button class="add-ledger-btn" :disabled="busy" @click="showCreateInput = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            新增账本
          </button>
        </template>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
.ledger-manage {
  padding: 4px 0;
}

.ledger-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ledger-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 10px;
  transition: background 0.15s;
}

.ledger-item:hover {
  background: var(--surface-soft, rgba(255, 255, 255, 0.04));
}

.ledger-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.ledger-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.default-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--blue, #5B8DEF);
  background: rgba(91, 141, 239, 0.12);
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
}

.rename-input {
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--s1, transparent);
  color: var(--text);
  font-size: 14px;
  outline: none;
}

.rename-input:focus {
  border-color: var(--blue, #5B8DEF);
}

.ledger-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.act-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  color: var(--muted);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.act-btn:hover:not(:disabled) {
  background: var(--surface-soft, rgba(255, 255, 255, 0.06));
  color: var(--text);
}

.act-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.act-btn.danger:hover:not(:disabled) {
  color: var(--red, #F05A55);
  background: rgba(240, 90, 85, 0.1);
}

.create-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border, rgba(255, 255, 255, 0.08));
}

.create-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.create-input {
  flex: 1;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--s1, transparent);
  color: var(--text);
  font-size: 14px;
  outline: none;
}

.create-input:focus {
  border-color: var(--blue, #5B8DEF);
}

.create-confirm-btn {
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 8px;
  background: var(--blue, #5B8DEF);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.create-confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.create-cancel-btn {
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.add-ledger-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--blue, #5B8DEF);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  width: 100%;
  justify-content: center;
}

.add-ledger-btn:hover:not(:disabled) {
  background: rgba(91, 141, 239, 0.06);
  border-color: var(--blue, #5B8DEF);
}

.add-ledger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
