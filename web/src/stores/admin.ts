import { defineStore } from 'pinia'
import { api } from '../shared/http'

interface CacheState<T> {
  data: T | null
  loadedAt: number
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    // 概览页状态
    overview: {
      data: null as any,
      loadedAt: 0,
    } as CacheState<any>,

    // 用户管理状态
    users: {
      items: [] as any[],
      total: 0,
      loadedAt: 0,
      // 保持之前的搜索/过滤/排序/分页位置
      query: '',
      sortBy: 'last_active_at',
      sortDir: 'desc' as 'asc' | 'desc',
      currentPage: 1,
      pageSize: 10,
      lastRequestKey: '',
    },

    // 邀请码管理状态
    invites: {
      items: [] as any[],
      total: 0,
      loadedAt: 0,
      inviteStatus: 'active' as 'active' | 'used',
      currentPage: 1,
      pageSize: 10,
      lastRequestKey: '',
    },

    // 运营配置状态
    ops: {
      configs: {} as Record<string, { text: string; image_url: string }>,
      appUpdate: { text: '', download_url: '' },
      loadedAt: 0,
      thumbLoadFailed: {} as Record<string, boolean>,
    }
  }),

  actions: {
    /**
     * 加载概览数据
     */
    async loadOverview(force = false) {
      // 缓存 30 秒
      const isFresh = Date.now() - this.overview.loadedAt < 30000
      if (!force && this.overview.data && isFresh) return

      const res = await api.get('/api/admin/overview')
      this.overview.data = res
      this.overview.loadedAt = Date.now()
    },

    /**
     * 加载用户列表
     */
    async loadUsers(force = false) {
      const offset = (this.users.currentPage - 1) * this.users.pageSize
      const key = [
        this.users.query,
        this.users.sortBy,
        this.users.sortDir,
        String(this.users.pageSize),
        String(offset),
        force ? '1' : '0'
      ].join('|')

      // 如果请求参数没变且没强制刷新，且有数据，则跳过
      if (!force && key === this.users.lastRequestKey && this.users.items.length > 0) return

      const params = new URLSearchParams({
        q: this.users.query,
        status: 'all',
        include_local: '0',
        sort_by: this.users.sortBy,
        sort_dir: this.users.sortDir,
        limit: String(this.users.pageSize),
        offset: String(offset),
      })
      if (force) params.set('force', '1')

      const res = await api.get<any>(`/api/admin/users?${params.toString()}`)
      this.users.items = res.items || []
      this.users.total = res.total || 0
      this.users.loadedAt = Date.now()
      this.users.lastRequestKey = key
    },

    /**
     * 加载邀请码
     */
    async loadInvites(force = false) {
      const offset = (this.invites.currentPage - 1) * this.invites.pageSize
      const key = [
        this.invites.inviteStatus,
        String(this.invites.pageSize),
        String(offset),
        force ? '1' : '0'
      ].join('|')

      if (!force && key === this.invites.lastRequestKey && this.invites.items.length > 0) return

      const params = new URLSearchParams({
        status: this.invites.inviteStatus,
        limit: String(this.invites.pageSize),
        offset: String(offset),
        random: '1', // 保持原有逻辑
      })
      if (force) params.set('force', '1')

      const res = await api.get<any>(`/api/admin/invites?${params.toString()}`)
      this.invites.items = res.items || []
      this.invites.total = res.total || 0
      this.invites.loadedAt = Date.now()
      this.invites.lastRequestKey = key
    },

    /**
     * 加载运营配置
     */
    async loadOpsConfigs(scenes: readonly string[], force = false) {
      const isFresh = Date.now() - this.ops.loadedAt < 60000 // 配置信息缓存 1 分钟
      if (!force && Object.keys(this.ops.configs).length > 0 && isFresh) return

      const promises = [
        ...scenes.map(async (scene) => {
          const path = `/api/admin/ops/${scene === 'invite' ? 'invite_acquire' : scene}`
          const res = await api.get<any>(path)
          this.ops.configs[scene] = {
            text: res?.text || '',
            image_url: res?.image_url || ''
          }
        }),
        (async () => {
          const res = await api.get<any>('/api/admin/ops/app_update')
          this.ops.appUpdate = {
            text: res?.text || '',
            download_url: res?.download_url || ''
          }
        })()
      ]

      await Promise.all(promises)
      this.ops.loadedAt = Date.now()
    }
  }
})
