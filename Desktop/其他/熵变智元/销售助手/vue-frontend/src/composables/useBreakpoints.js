import { ref, computed, onMounted, onUnmounted } from 'vue'

// 响应式断点管理
export function useBreakpoints() {
  const windowWidth = ref(window.innerWidth)
  
  // 断点定义
  const breakpoints = {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536
  }
  
  // 计算当前断点
  const currentBreakpoint = computed(() => {
    const width = windowWidth.value
    
    if (width >= breakpoints['2xl']) return '2xl'
    if (width >= breakpoints.xl) return 'xl'
    if (width >= breakpoints.lg) return 'lg'
    if (width >= breakpoints.md) return 'md'
    if (width >= breakpoints.sm) return 'sm'
    return 'xs'
  })
  
  // 各种设备类型判断
  const isMobile = computed(() => windowWidth.value < breakpoints.md)
  const isTablet = computed(() => 
    windowWidth.value >= breakpoints.md && windowWidth.value < breakpoints.lg
  )
  const isDesktop = computed(() => windowWidth.value >= breakpoints.lg)
  const isLargeScreen = computed(() => windowWidth.value >= breakpoints.xl)
  
  // 具体断点判断
  const isXs = computed(() => currentBreakpoint.value === 'xs')
  const isSm = computed(() => currentBreakpoint.value === 'sm')
  const isMd = computed(() => currentBreakpoint.value === 'md')
  const isLg = computed(() => currentBreakpoint.value === 'lg')
  const isXl = computed(() => currentBreakpoint.value === 'xl')
  const is2xl = computed(() => currentBreakpoint.value === '2xl')
  
  // 范围判断
  const isSmAndUp = computed(() => windowWidth.value >= breakpoints.sm)
  const isMdAndUp = computed(() => windowWidth.value >= breakpoints.md)
  const isLgAndUp = computed(() => windowWidth.value >= breakpoints.lg)
  const isXlAndUp = computed(() => windowWidth.value >= breakpoints.xl)
  
  const isSmAndDown = computed(() => windowWidth.value < breakpoints.md)
  const isMdAndDown = computed(() => windowWidth.value < breakpoints.lg)
  const isLgAndDown = computed(() => windowWidth.value < breakpoints.xl)
  
  // 更新窗口宽度
  const updateWidth = () => {
    windowWidth.value = window.innerWidth
  }
  
  // 生命周期管理
  onMounted(() => {
    window.addEventListener('resize', updateWidth)
  })
  
  onUnmounted(() => {
    window.removeEventListener('resize', updateWidth)
  })
  
  return {
    // 原始数据
    windowWidth: readonly(windowWidth),
    breakpoints: readonly(breakpoints),
    currentBreakpoint,
    
    // 设备类型
    isMobile,
    isTablet,
    isDesktop,
    isLargeScreen,
    
    // 具体断点
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2xl,
    
    // 范围判断
    isSmAndUp,
    isMdAndUp,
    isLgAndUp,
    isXlAndUp,
    isSmAndDown,
    isMdAndDown,
    isLgAndDown
  }
}

// 只读工具函数
function readonly(ref) {
  return computed(() => ref.value)
}

