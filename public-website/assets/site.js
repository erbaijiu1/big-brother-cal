(() => {
  'use strict'

  const $ = (selector) => document.querySelector(selector)
  const form = $('#quote-form')

  // Reveal sections only after JavaScript is confirmed available.
  const revealItems = [...document.querySelectorAll('[data-reveal]')]
  if (revealItems.length && 'IntersectionObserver' in window) {
    document.body.classList.add('reveal-ready')

    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return

        entry.target.classList.add('is-visible')
        observer.unobserve(entry.target)
      })
    }, { threshold: 0.14 })

    revealItems.forEach((item) => revealObserver.observe(item))
  }

  $('#current-year').textContent = new Date().getFullYear()
  if (!form) return

  const elements = {
    apiStatus: $('#api-status'),
    category: $('#category'),
    categoryDescription: $('#category-description'),
    quantity: $('#quantity'),
    weight: $('#weight'),
    length: $('#length'),
    width: $('#width'),
    height: $('#height'),
    volume: $('#volume'),
    chargeWeightTip: $('#charge-weight-tip'),
    district: $('#district'),
    subDistrict: $('#sub-district'),
    remoteTip: $('#remote-tip'),
    upstairsOptions: $('#upstairs-options'),
    submit: $('#quote-submit'),
    error: $('#form-error'),
    results: $('#quote-results'),
    resultList: $('#result-list'),
    closeResults: $('#close-results')
  }

  const state = {
    categories: [],
    districts: [],
    categoryReady: false,
    districtReady: false
  }

  function numberValue(input, fallback = 0) {
    const value = Number(input.value)
    return Number.isFinite(value) && value >= 0 ? value : fallback
  }

  function setStatus(message, type = '') {
    elements.apiStatus.textContent = message
    elements.apiStatus.className = `api-status ${type}`.trim()
  }

  function setError(message = '') {
    elements.error.textContent = message
    elements.error.hidden = !message
  }

  function updateReadyState() {
    const ready = state.categoryReady && state.districtReady
    elements.submit.disabled = !ready
    if (ready) setStatus('报价服务连接正常，分类与香港地区数据已加载。', 'ready')
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options
    })

    if (!response.ok) throw new Error(`接口返回 ${response.status}`)
    return response.json()
  }

  async function loadCategories() {
    const payload = await requestJson('/cal_price/classify/classify_list', {
      method: 'POST',
      body: '{}'
    })
    if (payload.code !== 200 || !Array.isArray(payload.data)) throw new Error('分类数据格式不正确')

    state.categories = payload.data
    elements.category.replaceChildren(new Option('请选择货物分类', ''))
    payload.data.forEach((item) => {
      const option = new Option(item.main_category, item.category_id)
      option.dataset.description = item.sub_examples || ''
      elements.category.add(option)
    })
    elements.category.disabled = false
    state.categoryReady = true
  }

  async function loadDistricts() {
    const payload = await requestJson('/cal_price/public/districts')
    const districts = Array.isArray(payload) ? payload : payload.data
    if (!Array.isArray(districts)) throw new Error('地区数据格式不正确')

    state.districts = districts
    elements.district.replaceChildren(new Option('请选择香港行政区', ''))
    districts.forEach((item) => {
      elements.district.add(new Option(item.name_cn, item.id))
    })
    elements.district.disabled = false
    state.districtReady = true
  }

  async function initializeQuote() {
    const results = await Promise.allSettled([loadCategories(), loadDistricts()])
    const failed = results.filter((result) => result.status === 'rejected')

    if (failed.length) {
      console.error('报价基础数据加载失败', failed)
      setStatus('报价服务暂时无法连接，请稍后刷新，或通过企业邮箱联系客服。', 'error')
      return
    }
    updateReadyState()
  }

  elements.category.addEventListener('change', () => {
    const option = elements.category.selectedOptions[0]
    elements.categoryDescription.textContent = option?.dataset.description
      ? `常见示例：${option.dataset.description}`
      : '请选择最接近的货物分类'
  })

  elements.district.addEventListener('change', () => {
    const district = state.districts.find((item) => String(item.id) === elements.district.value)
    const subs = district?.subs || []

    elements.subDistrict.replaceChildren(new Option(subs.length ? '请选择分区 / 地段' : '该行政区暂无细分地区', ''))
    subs.forEach((item) => {
      const option = new Option(item.name_cn, item.id)
      option.dataset.remote = item.is_remote ? '1' : '0'
      elements.subDistrict.add(option)
    })
    elements.subDistrict.disabled = !subs.length
    elements.remoteTip.textContent = ''
  })

  elements.subDistrict.addEventListener('change', () => {
    const option = elements.subDistrict.selectedOptions[0]
    if (!elements.subDistrict.value) {
      elements.remoteTip.textContent = ''
      return
    }
    elements.remoteTip.textContent = option?.dataset.remote === '1' ? '该地段可能适用偏远地区附加费' : '该地段当前未标记为偏远地区'
  })

  function updateVolumeAndChargeWeight(event) {
    const dimensions = [elements.length, elements.width, elements.height].map((input) => numberValue(input))
    if (dimensions.every((value) => value > 0) && event?.target !== elements.volume) {
      elements.volume.value = ((dimensions[0] * dimensions[1] * dimensions[2]) / 1000000).toFixed(6)
    }

    const weight = numberValue(elements.weight)
    const volume = numberValue(elements.volume)
    if (!weight && !volume) {
      elements.chargeWeightTip.textContent = '实重或体积至少填写一项；体积重按体积 × 200 参考计算'
      return
    }

    const volumeWeight = volume * 200
    const chargeWeight = Math.max(weight, volumeWeight)
    elements.chargeWeightTip.textContent = `参考计费重量 ${chargeWeight.toFixed(2)} kg（实重 ${weight.toFixed(2)} kg / 体积重 ${volumeWeight.toFixed(2)} kg，取较大值）`
  }

  ;[elements.weight, elements.length, elements.width, elements.height, elements.volume].forEach((input) => {
    input.addEventListener('input', updateVolumeAndChargeWeight)
  })

  form.addEventListener('change', (event) => {
    if (event.target.name === 'upstairs') {
      elements.upstairsOptions.hidden = event.target.value !== '1'
    }
  })

  function selectedRadio(name) {
    return form.querySelector(`input[name="${name}"]:checked`)?.value || '0'
  }

  function buildRequest() {
    const selectedSub = elements.subDistrict.selectedOptions[0]
    const needUpstairs = selectedRadio('upstairs')

    return {
      category_id: Number(elements.category.value),
      weight: numberValue(elements.weight),
      volume: numberValue(elements.volume),
      quantity: Math.max(1, Math.floor(numberValue(elements.quantity, 1))),
      extra_fee_data: {
        type: '袋装',
        need_go_upstairs: needUpstairs,
        district: Number(elements.district.value),
        sub_district: elements.subDistrict.value ? Number(elements.subDistrict.value) : null,
        is_remote: selectedSub?.dataset.remote === '1',
        has_elevator: needUpstairs === '1' ? selectedRadio('elevator') : '0',
        need_stairs: needUpstairs === '1' ? selectedRadio('stairs') : '0',
        input_mode: 'lwh',
        length: numberValue(elements.length),
        width: numberValue(elements.width),
        height: numberValue(elements.height)
      }
    }
  }

  function validateRequest(data) {
    if (!data.category_id) return '请选择货物分类。'
    if (!data.weight && !data.volume) return '请填写货物实重，或填写体积/长宽高。'
    if (!data.extra_fee_data.district) return '请选择香港收货行政区。'
    return ''
  }

  function addTextRow(parent, label, value) {
    const row = document.createElement('div')
    row.className = 'fee-row'
    const name = document.createElement('span')
    const amount = document.createElement('strong')
    name.textContent = label
    amount.textContent = value
    row.append(name, amount)
    parent.append(row)
  }

  function renderResults(quotes) {
    elements.resultList.replaceChildren()

    if (!quotes.length) {
      const empty = document.createElement('div')
      empty.className = 'result-empty'
      empty.textContent = '当前资料未匹配到可用报价方案，请联系企业客服进一步确认。'
      elements.resultList.append(empty)
    }

    quotes.slice(0, 3).forEach((quote, index) => {
      const card = document.createElement('article')
      card.className = 'result-card'

      const head = document.createElement('div')
      head.className = 'result-card-head'
      const label = document.createElement('div')
      const plan = document.createElement('small')
      const channel = document.createElement('strong')
      const price = document.createElement('span')
      plan.textContent = index === 0 ? '优先参考方案' : `参考方案 ${index + 1}`
      channel.textContent = [quote.channel, quote.transport_method].filter(Boolean).join(' · ')
      price.className = 'result-price'
      price.textContent = `${Number(quote.total_price || 0).toFixed(2)} 元`
      label.append(plan, channel)
      head.append(label, price)
      card.append(head)

      const fees = document.createElement('div')
      fees.className = 'fee-list'
      ;(quote.fee_details || []).forEach((fee) => {
        addTextRow(fees, fee.cn_name || fee.name || '费用', `${fee.amount ?? '--'} 元`)
      })
      if (fees.childElementCount) card.append(fees)

      if (quote.remark) {
        const remark = document.createElement('p')
        remark.className = 'result-remark'
        remark.textContent = `说明：${quote.remark}`
        card.append(remark)
      }
      elements.resultList.append(card)
    })

    elements.results.hidden = false
    elements.results.scrollTop = 0
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    setError()

    const data = buildRequest()
    const validationMessage = validateRequest(data)
    if (validationMessage) {
      setError(validationMessage)
      return
    }

    const previousLabel = elements.submit.querySelector('span').textContent
    elements.submit.disabled = true
    elements.submit.querySelector('span').textContent = '正在计算…'

    try {
      const payload = await requestJson('/cal_price/pricing_rule/min_pricing', {
        method: 'POST',
        body: JSON.stringify(data)
      })
      if (payload.code !== 200 || !Array.isArray(payload.data)) throw new Error(payload.message || '报价数据格式不正确')
      renderResults(payload.data)
    } catch (error) {
      console.error('报价失败', error)
      setError('报价服务暂时不可用，请稍后重试或通过企业邮箱联系客服。')
    } finally {
      elements.submit.disabled = false
      elements.submit.querySelector('span').textContent = previousLabel
    }
  })

  elements.closeResults.addEventListener('click', () => {
    elements.results.hidden = true
  })

  initializeQuote()
})()
