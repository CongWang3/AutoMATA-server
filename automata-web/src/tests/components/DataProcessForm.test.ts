/**
 * DataProcessForm 组件单元测试
 */
import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import DataProcessForm from '@/components/DataProcessForm.vue'

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    }
  }
})

// Mock WebSocket service
vi.mock('@/api/websocket', () => ({
  webSocketService: {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    setOnProgress: vi.fn()
  }
}))

describe('DataProcessForm', () => {
  const defaultProps = {
    title: '测试标题',
    subtitle: 'Test Subtitle',
    fileLabel: '上传文件',
    fileTip: '文件提示信息',
    nomenclatureLabel: '命名方式',
    nomenclaturePlaceholder: '请选择命名方式',
    nomenclatureOptions: [
      { label: '选项1', value: 'option1' },
      { label: '选项2', value: 'option2' }
    ],
    speciesOptions: [
      { label: '物种1', value: 'species1' },
      { label: '物种2', value: 'species2' }
    ],
    onSubmit: vi.fn().mockResolvedValue({ job_id: 'test123', status: 'success' })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基本渲染', () => {
    it('应该正确渲染标题和副标题', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      expect(wrapper.text()).toContain('测试标题')
      expect(wrapper.text()).toContain('Test Subtitle')
    })

    it('应该正确渲染文件上传区域', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const uploadComponent = wrapper.findComponent({ name: 'ElUpload' })
      expect(uploadComponent.exists()).toBe(true)
      expect(wrapper.text()).toContain('上传文件')
    })

    it('应该正确渲染选择框', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const selectComponents = wrapper.findAllComponents({ name: 'ElSelect' })
      expect(selectComponents).toHaveLength(3) // 命名方式、数据类型、物种
    })
  })

  describe('示例数据下载', () => {
    it('当提供示例数据URL时应该显示下载按钮', () => {
      const props = {
        ...defaultProps,
        exampleDataUrl: '/test/example.txt',
        exampleFileName: 'test_example.txt'
      }

      const wrapper = mount(DataProcessForm, {
        props
      })

      const downloadButton = wrapper.find('.example-btn')
      expect(downloadButton.exists()).toBe(true)
      expect(downloadButton.text()).toContain('下载示例数据')
    })

    it('当没有示例数据URL时不显示下载按钮', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const downloadButton = wrapper.find('.example-btn')
      expect(downloadButton.exists()).toBe(false)
    })

    it('点击下载按钮应该触发文件下载', async () => {
      const props = {
        ...defaultProps,
        exampleDataUrl: '/test/example.txt',
        exampleFileName: 'test_example.txt'
      }

      const wrapper = mount(DataProcessForm, {
        props
      })

      // Mock createElement 和 click
      const createElementSpy = vi.spyOn(document, 'createElement')
      const appendChildSpy = vi.spyOn(document.body, 'appendChild')
      const removeChildSpy = vi.spyOn(document.body, 'removeChild')

      const mockLink = {
        href: '',
        download: '',
        style: { display: '' },
        click: vi.fn()
      }
      createElementSpy.mockReturnValue(mockLink as any)

      const downloadButton = wrapper.find('.example-btn')
      await downloadButton.trigger('click')

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(mockLink.href).toBe('/test/example.txt')
      expect(mockLink.download).toBe('test_example.txt')
      expect(mockLink.click).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('示例数据已开始下载: test_example.txt')

      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })

  describe('文件上传验证', () => {
    it('应该拒绝不支持的文件类型', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const testFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      const result = (wrapper.vm as any).beforeUpload(testFile)

      expect(result).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('只支持 txt、csv、tsv 格式的文件！')
    })

    it('应该接受支持的文件类型', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const testFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      const result = (wrapper.vm as any).beforeUpload(testFile)

      expect(result).toBe(true)
    })

    it('应该拒绝过大的文件', () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      // 创建一个大于10MB的文件
      const largeContent = 'a'.repeat(11 * 1024 * 1024) // 11MB
      const testFile = new File([largeContent], 'test.txt', { type: 'text/plain' })
      const result = (wrapper.vm as any).beforeUpload(testFile)

      expect(result).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('文件大小不能超过10MB')
    })
  })

  describe('表单提交', () => {
    it('应该验证必填字段', async () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const submitButton = wrapper.find('.submit-btn')
      await submitButton.trigger('click')

      // 应该显示验证错误
      expect(ElMessage.error).toHaveBeenCalledWith('请上传文件')
    })

    it('应该成功提交有效表单', async () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      // 模拟文件上传
      const testFile = new File(['gene1\t100\t200'], 'test.txt', { type: 'text/plain' })
      ;(wrapper.vm as any).formData.file = testFile
      ;(wrapper.vm as any).formData.nomenclature = 'option1'
      ;(wrapper.vm as any).formData.dataType = 'FPKM'
      ;(wrapper.vm as any).formData.organism = 'species1'

      const submitButton = wrapper.find('.submit-btn')
      await submitButton.trigger('click')

      // 等待异步操作完成
      await wrapper.vm.$nextTick()

      expect(defaultProps.onSubmit).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalled()
    })
  })

  describe('WebSocket进度更新', () => {
    it('应该在提交时连接WebSocket', async () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      // 模拟文件上传
      const testFile = new File(['gene1\t100\t200'], 'test.txt', { type: 'text/plain' })
      ;(wrapper.vm as any).formData.file = testFile
      ;(wrapper.vm as any).formData.nomenclature = 'option1'
      ;(wrapper.vm as any).formData.dataType = 'FPKM'
      ;(wrapper.vm as any).formData.organism = 'species1'

      await (wrapper.vm as any).submitForm()

      const { webSocketService } = await import('@/api/websocket')
      expect(webSocketService.connect).toHaveBeenCalled()
      expect(webSocketService.setOnProgress).toHaveBeenCalled()
    })

    it('应该正确处理进度消息', async () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      const progressCallback = vi.fn()
      const { webSocketService } = await import('@/api/websocket')
      ;(webSocketService.setOnProgress as any).mockImplementation(progressCallback)

      await (wrapper.vm as any).connectProgressWebSocket()

      // 模拟进度消息
      const progressMessage = {
        event: 'upload_progress',
        progress_percent: 75,
        message: '处理中...'
      }

      // 调用进度回调
      if (progressCallback.mock.calls[0]) {
        progressCallback.mock.calls[0][0](progressMessage)
        expect((wrapper.vm as any).progressPercentage).toBe(75)
        expect((wrapper.vm as any).progressMessage).toBe('处理中...')
      }
    })
  })

  describe('表单重置', () => {
    it('应该能够重置表单', async () => {
      const wrapper = mount(DataProcessForm, {
        props: defaultProps
      })

      // 设置一些表单值
      ;(wrapper.vm as any).formData.nomenclature = 'option1'
      ;(wrapper.vm as any).formData.email = 'test@example.com'

      await (wrapper.vm as any).resetForm()

      expect((wrapper.vm as any).formData.nomenclature).toBe('')
      expect((wrapper.vm as any).formData.email).toBe('')
    })
  })
})