/**
 * 历史兼容入口。
 *
 * Web 页面、布局和路由已经统一走 ../stores/composables.ts。
 * 这里不再保留第二套状态实现，只负责兼容旧导入路径，
 * 防止后面的人误以为这里还能继续长新逻辑。
 */

export { useKonaStore } from '../stores/composables'
