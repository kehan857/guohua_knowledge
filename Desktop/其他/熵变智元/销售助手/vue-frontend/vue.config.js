const { defineConfig } = require('@vue/cli-service')
const path = require('path')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // 基础路径
  publicPath: process.env.NODE_ENV === 'production' ? '/admin/' : '/',
  
  // 输出目录
  outputDir: 'dist',
  
  // 静态资源目录
  assetsDir: 'static',
  
  // 生产环境去除console
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        'components': path.resolve(__dirname, 'src/components'),
        'views': path.resolve(__dirname, 'src/views'),
        'utils': path.resolve(__dirname, 'src/utils'),
        'api': path.resolve(__dirname, 'src/api'),
        'styles': path.resolve(__dirname, 'src/styles')
      }
    },
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          libs: {
            name: 'chunk-libs',
            test: /[\\/]node_modules[\\/]/,
            priority: 10,
            chunks: 'initial'
          },
          elementPlus: {
            name: 'chunk-elementPlus',
            priority: 20,
            test: /[\\/]node_modules[\\/]_?element-plus(.*)/
          },
          commons: {
            name: 'chunk-commons',
            test: path.resolve(__dirname, 'src/components'),
            minChunks: 3,
            priority: 5,
            reuseExistingChunk: true
          }
        }
      }
    }
  },
  
  // 开发服务器配置
  devServer: {
    port: 8080,
    open: true,
    host: '0.0.0.0',
    https: false,
    client: {
      webSocketURL: 'ws://localhost:8080/ws',
    },
    
    // 代理配置
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000',
        changeOrigin: true,
        ws: true,
        pathRewrite: {
          '^/api': '/api'
        }
      },
      '/socket.io': {
        target: process.env.VUE_APP_WS_URL || 'ws://localhost:3000',
        changeOrigin: true,
        ws: true
      }
    }
  },
  
  // CSS相关配置
  css: {
    loaderOptions: {
      scss: {
        additionalData: `
          @import "@/styles/variables.scss";
        `
      }
    }
  },
  
  // 生产环境优化
  chainWebpack: config => {
    // 预加载优化
    if (config.plugins.has('preload')) {
      config.plugin('preload').tap(() => [
        {
          rel: 'preload',
          include: 'initial',
          fileBlacklist: [/\.map$/, /hot-update\.js$/, /runtime\..*\.js$/]
        }
      ])
    }
    
    // 预获取优化
    if (config.plugins.has('prefetch')) {
      config.plugin('prefetch').tap(() => [
        {
          rel: 'prefetch',
          include: 'asyncChunks'
        }
      ])
    }
    
    // 生产环境压缩图片
    if (process.env.NODE_ENV === 'production') {
      config.module
        .rule('images')
        .test(/\.(gif|png|jpe?g|svg)$/i)
        .use('image-webpack-loader')
        .loader('image-webpack-loader')
        .options({
          mozjpeg: { progressive: true, quality: 65 },
          optipng: { enabled: false },
          pngquant: { quality: [0.65, 0.90], speed: 4 },
          gifsicle: { interlaced: false }
        })
    }
    
    // SVG图标处理
    config.module
      .rule('svg')
      .exclude.add(path.resolve(__dirname, 'src/icons'))
      .end()
    
    config.module
      .rule('icons')
      .test(/\.svg$/)
      .include.add(path.resolve(__dirname, 'src/icons'))
      .end()
      .use('svg-sprite-loader')
      .loader('svg-sprite-loader')
      .options({
        symbolId: 'icon-[name]'
      })
      .end()
  },
  
  // PWA配置
  pwa: {
    name: '熵变智元AI销售助手',
    themeColor: '#3b82f6',
    msTileColor: '#000000',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    
    workboxPluginMode: 'InjectManifest',
    workboxOptions: {
      swSrc: 'src/pwa/sw.js'
    },
    
    manifestOptions: {
      background_color: '#ffffff',
      icons: [
        {
          src: 'img/icons/android-chrome-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: 'img/icons/android-chrome-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    }
  },
  
  // 插件配置
  pluginOptions: {
    // 自动导入配置
    'style-resources-loader': {
      preProcessor: 'scss',
      patterns: [
        path.resolve(__dirname, 'src/styles/variables.scss'),
        path.resolve(__dirname, 'src/styles/mixins.scss')
      ]
    }
  }
})

