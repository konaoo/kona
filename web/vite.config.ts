import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const resolvePath = (path: string) => fileURLToPath(new URL(path, import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const buildTarget = process.env.VITE_BUILD_TARGET === 'admin' ? 'admin' : 'app'
  const isBuild = command === 'build'
  const isAdminBuild = isBuild && buildTarget === 'admin'
  const buildRoot = isBuild ? resolvePath(isAdminBuild ? './admin' : './app') : undefined

  return {
    root: buildRoot,
    plugins: [vue()],
    publicDir: resolvePath('./public'),
    resolve: {
      alias: {
        '@': resolvePath('./src'),
      },
    },
    base: isAdminBuild ? '/admin/' : '/',
    build: isBuild
      ? {
          outDir: resolvePath(isAdminBuild ? './dist/admin' : './dist/app'),
        }
      : undefined,
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:52345',
          changeOrigin: true,
          secure: false,
          ws: true,
        },
      },
    },
  }
})
