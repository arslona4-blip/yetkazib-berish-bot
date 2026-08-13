import { useEffect, useMemo, useState } from 'react'
import {
  api,
  clearAuth,
  loadAuth,
  saveAuth,
  type AuthState,
} from './api'
import type {
  CartLine,
  CatalogCategory,
  Category,
  Contact,
  DebtEntry,
  MorePanel,
  Movement,
  Order,
  OrderItem,
  Product,
  Promo,
  RangeReport,
  StatsPayload,
  Tab,
} from './types'
import './styles.css'

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string
        ready?: () => void
        expand?: () => void
        platform?: string
        themeParams?: Record<string, string>
      }
    }
  }
}

function readTgInitData(): string {
  return (window.Telegram?.WebApp?.initData || '').trim()
}

const REASON: Record<string, string> = {
  sale: '🛒 Sotuv',
  in: '📥 Kirim',
  out: '📤 Chiqim',
  inventory: '📋 Inventar',
  adjust: '✏️ Tuzatish',
}

const ORDER_FILTERS: [string, string][] = [
  ['new', 'Yangi'],
  ['active', 'Faol'],
  ['delivered', 'Yetkazilgan'],
  ['cancelled', 'Bekor'],
]

function money(n: number) {
  return `${Number(n || 0).toLocaleString('uz-UZ')} so‘m`
}

function isKassaOnlyMode() {
  try {
    return new URLSearchParams(window.location.search).get('mode') === 'kassa'
  } catch {
    return false
  }
}

export default function App() {
  const kassaOnly = isKassaOnlyMode()
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [tab, setTab] = useState<Tab>(kassaOnly ? 'kassa' : 'dash')
  const [shop, setShop] = useState('Admin')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [lastSync, setLastSync] = useState('')
  const [stats, setStats] = useState<StatsPayload | null>(null)
  const [orderStatus, setOrderStatus] = useState('new')
  const [orderQuery, setOrderQuery] = useState('')
  const [orders, setOrders] = useState<Order[]>([])
  const [payments, setPayments] = useState<Order[]>([])
  const [openOrderId, setOpenOrderId] = useState<number | null>(null)
  const [orderItems, setOrderItems] = useState<OrderItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [catalog, setCatalog] = useState<Product[]>([])
  const [selectedCat, setSelectedCat] = useState<number | 'all'>('all')
  const [lowOnly, setLowOnly] = useState(false)
  const [moves, setMoves] = useState<Movement[]>([])
  const [stockForm, setStockForm] = useState({
    product_id: 0,
    mode: 'in',
    qty: 1,
    note: '',
  })
  const [pinForm, setPinForm] = useState({ adminId: '', pin: '', code: '' })
  const [priceEdit, setPriceEdit] = useState<Record<number, string>>({})
  const [morePanel, setMorePanel] = useState<MorePanel>('broadcast')
  const [broadcastText, setBroadcastText] = useState('')
  const [broadcastResult, setBroadcastResult] = useState('')
  const [csvText, setCsvText] = useState('')
  const [csvInfo, setCsvInfo] = useState('')
  const [contacts, setContacts] = useState<Contact[]>([])
  const [contactForm, setContactForm] = useState({
    name: '',
    phone: '',
    note: '',
  })
  const [cart, setCart] = useState<CartLine[]>([])
  const [kassaSearch, setKassaSearch] = useState('')
  const [kassaBarcode, setKassaBarcode] = useState('')
  const [kassaPay, setKassaPay] = useState<'cash' | 'card' | 'debt'>('cash')
  const [kassaCustomer, setKassaCustomer] = useState('')
  const [kassaPhone, setKassaPhone] = useState('')
  const [kassaPromo, setKassaPromo] = useState('')
  const [kassaContactId, setKassaContactId] = useState(0)
  const [kassaMsg, setKassaMsg] = useState('')
  const [debtors, setDebtors] = useState<Contact[]>([])
  const [debtTotals, setDebtTotals] = useState({
    debts: 0,
    payments: 0,
    open: 0,
  })
  const [debtContactId, setDebtContactId] = useState<number | null>(null)
  const [debtEntries, setDebtEntries] = useState<DebtEntry[]>([])
  const [debtBalance, setDebtBalance] = useState(0)
  const [debtForm, setDebtForm] = useState({
    amount: '',
    kind: 'payment' as 'debt' | 'payment',
    note: '',
  })
  const [promos, setPromos] = useState<Promo[]>([])
  const [promoForm, setPromoForm] = useState({
    code: '',
    discount_percent: '10',
    discount_amount: '0',
    min_order: '0',
  })
  const [reportFrom, setReportFrom] = useState(() =>
    new Date().toISOString().slice(0, 10),
  )
  const [reportTo, setReportTo] = useState(() =>
    new Date().toISOString().slice(0, 10),
  )
  const [report, setReport] = useState<RangeReport | null>(null)
  const [catalogCats, setCatalogCats] = useState<CatalogCategory[]>([])
  const [productForm, setProductForm] = useState({
    name: '',
    price: '',
    stock: '0',
    barcode: '',
    category_id: '',
    description: '',
  })
  const [newCatName, setNewCatName] = useState('')
  const [showProductForm, setShowProductForm] = useState(false)
  const [tgInit, setTgInit] = useState('')
  const [tgReady, setTgReady] = useState(false)
  const [showCode, setShowCode] = useState(false)
  const [booting, setBooting] = useState(true)
  const [menuOpen, setMenuOpen] = useState(false)

  const cartTotal = useMemo(
    () => cart.reduce((s, l) => s + l.price * l.quantity, 0),
    [cart],
  )

  const kassaFiltered = useMemo(() => {
    const q = kassaSearch.trim().toLowerCase()
    const list = catalog.filter((p) => p.is_active && p.stock > 0)
    if (!q) return list.slice(0, 40)
    return list
      .filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.barcode || '').includes(q) ||
          String(p.id) === q,
      )
      .slice(0, 40)
  }, [catalog, kassaSearch])

  const initials = useMemo(() => {
    const raw = (shop || 'AD').trim()
    const parts = raw.split(/\s+/).filter(Boolean)
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return raw.slice(0, 2).toUpperCase()
  }, [shop])

  async function bootstrap(a: AuthState) {
    setBusy(true)
    setError('')
    try {
      const me = await api.me(a)
      setShop(me.shop_name || 'Admin')
      saveAuth(a)
      setAuth(a)
      await refreshAll(a)
    } catch (e) {
      clearAuth()
      setAuth(null)
      setError(e instanceof Error ? e.message : 'Kirish xato')
    } finally {
      setBusy(false)
      setBooting(false)
    }
  }

  async function loginWithCode() {
    setBusy(true)
    setError('')
    try {
      const res = await api.login(Number(pinForm.adminId), pinForm.code.trim())
      const next: AuthState = {
        mode: 'session',
        session: res.session,
        adminId: res.admin_id,
      }
      setShop(res.shop_name || 'Admin')
      saveAuth(next)
      setAuth(next)
      await refreshAll(next)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kod xato')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    let cancelled = false

    async function start() {
      window.Telegram?.WebApp?.ready?.()
      window.Telegram?.WebApp?.expand?.()

      let data = ''
      for (let i = 0; i < 25; i++) {
        data = readTgInitData()
        if (data) break
        await new Promise((r) => setTimeout(r, 80))
      }
      if (cancelled) return

      setTgInit(data)
      setTgReady(true)

      if (data) {
        await bootstrap({ mode: 'tg', initData: data })
        return
      }

      const saved = loadAuth()
      if (saved?.mode === 'session' && saved.session) {
        await bootstrap(saved)
        return
      }
      if (saved?.mode === 'pin' && saved.pin && saved.adminId) {
        await bootstrap(saved)
        return
      }
      clearAuth()
      setAuth(null)
      setBooting(false)
    }

    void start()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function refreshAll(a: AuthState | null = auth, silent = false) {
    if (!a) return
    if (!silent) setBusy(true)
    setError('')
    try {
      const [st, or, pay, cats, prods, mv, cat] = await Promise.all([
        api.stats(a),
        api.orders(a, orderStatus, orderQuery),
        api.orders(a, 'payments'),
        api.whCategories(a, lowOnly),
        api.whProducts(a, selectedCat === 'all' ? undefined : selectedCat, lowOnly),
        api.whMoves(a),
        api.products(a),
      ])
      setStats(st)
      setOrders(or.orders)
      setPayments(pay.orders)
      setCategories(cats.categories)
      setProducts(prods.products)
      setMoves(mv.movements)
      setCatalog(cat.products)
      setLastSync(new Date().toLocaleTimeString('uz-UZ'))
    } catch (e) {
      if (!silent) setError(e instanceof Error ? e.message : 'Yuklash xato')
    } finally {
      if (!silent) setBusy(false)
    }
  }

  useEffect(() => {
    if (!auth) return
    const id = window.setInterval(() => {
      void refreshAll(auth, true)
    }, 20000)
    return () => window.clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth, orderStatus, orderQuery, lowOnly, selectedCat])

  useEffect(() => {
    if (!auth) return
    void (async () => {
      try {
        const or = await api.orders(auth, orderStatus, orderQuery)
        setOrders(or.orders)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Buyurtmalar xato')
      }
    })()
  }, [orderStatus, orderQuery, auth])

  useEffect(() => {
    if (!auth) return
    void (async () => {
      try {
        const [cats, prods] = await Promise.all([
          api.whCategories(auth, lowOnly),
          api.whProducts(
            auth,
            selectedCat === 'all' ? undefined : selectedCat,
            lowOnly,
          ),
        ])
        setCategories(cats.categories)
        setProducts(prods.products)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Ombor xato')
      }
    })()
  }, [lowOnly, selectedCat, auth])

  const filteredProducts = useMemo(() => products, [products])

  async function changeStatus(orderId: number, status: string) {
    if (!auth) return
    setBusy(true)
    try {
      await api.setStatus(auth, orderId, status)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Status xato')
    } finally {
      setBusy(false)
    }
  }

  async function changePayment(orderId: number, action: 'confirm' | 'reject') {
    if (!auth) return
    setBusy(true)
    try {
      await api.setPayment(auth, orderId, action)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'To‘lov xato')
    } finally {
      setBusy(false)
    }
  }

  async function removeOrder(orderId: number) {
    if (!auth) return
    if (!window.confirm(`#${orderId} o‘chirilsinmi?`)) return
    setBusy(true)
    try {
      await api.deleteOrder(auth, orderId)
      setOpenOrderId(null)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'O‘chirish xato')
    } finally {
      setBusy(false)
    }
  }

  async function toggleDetail(orderId: number) {
    if (!auth) return
    if (openOrderId === orderId) {
      setOpenOrderId(null)
      setOrderItems([])
      return
    }
    try {
      const detail = await api.orderDetail(auth, orderId)
      setOpenOrderId(orderId)
      setOrderItems(detail.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Tafsilot xato')
    }
  }

  async function submitStock() {
    if (!auth || !stockForm.product_id) return
    setBusy(true)
    try {
      await api.whStock(auth, {
        product_id: stockForm.product_id,
        mode: stockForm.mode,
        qty: Number(stockForm.qty),
        note: stockForm.note,
      })
      setStockForm((s) => ({ ...s, qty: 1, note: '' }))
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ombor xato')
    } finally {
      setBusy(false)
    }
  }

  async function quickIn(productId: number, qty: number) {
    if (!auth) return
    setBusy(true)
    try {
      await api.whStock(auth, {
        product_id: productId,
        mode: 'in',
        qty,
        note: 'Tezkor kirim',
      })
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kirim xato')
    } finally {
      setBusy(false)
    }
  }

  async function toggleProduct(p: Product) {
    if (!auth) return
    setBusy(true)
    try {
      await api.patchProduct(auth, p.id, { is_active: !p.is_active })
      const cat = await api.products(auth)
      setCatalog(cat.products)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mahsulot xato')
    } finally {
      setBusy(false)
    }
  }

  async function savePrice(p: Product) {
    if (!auth) return
    const raw = priceEdit[p.id]
    if (raw === undefined) return
    const price = Number(raw)
    if (!Number.isFinite(price) || price < 0) {
      setError('Narx noto‘g‘ri')
      return
    }
    setBusy(true)
    try {
      await api.patchProduct(auth, p.id, { price })
      setPriceEdit((s) => {
        const next = { ...s }
        delete next[p.id]
        return next
      })
      const cat = await api.products(auth)
      setCatalog(cat.products)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Narx xato')
    } finally {
      setBusy(false)
    }
  }

  async function loadContacts() {
    if (!auth) return
    try {
      const res = await api.contacts(auth)
      setContacts(res.contacts)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kontaktlar xato')
    }
  }

  useEffect(() => {
    if (auth && tab === 'more' && morePanel === 'contacts') {
      void loadContacts()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth, tab, morePanel])

  async function sendBroadcast() {
    if (!auth || !broadcastText.trim()) return
    if (!window.confirm('Barcha foydalanuvchilarga yuborilsinmi?')) return
    setBusy(true)
    setBroadcastResult('')
    try {
      const res = await api.broadcast(auth, broadcastText.trim())
      setBroadcastResult(
        `Yuborildi: ${res.sent}/${res.total} (xato: ${res.failed})`,
      )
      setBroadcastText('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Broadcast xato')
    } finally {
      setBusy(false)
    }
  }

  async function downloadCsv() {
    if (!auth) return
    setBusy(true)
    try {
      const text = await api.exportCsv(auth)
      setCsvText(text)
      setCsvInfo(`Eksport: ${text.split('\n').length - 1} qator`)
      const blob = new Blob([text], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'products.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export xato')
    } finally {
      setBusy(false)
    }
  }

  async function uploadCsv() {
    if (!auth || !csvText.trim()) return
    setBusy(true)
    try {
      const res = await api.importCsv(auth, csvText)
      setCsvInfo(`Import: ${res.imported} qator`)
      const cat = await api.products(auth)
      setCatalog(cat.products)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import xato')
    } finally {
      setBusy(false)
    }
  }

  async function addContact() {
    if (!auth || !contactForm.name.trim()) return
    setBusy(true)
    try {
      await api.createContact(auth, {
        name: contactForm.name.trim(),
        phone: contactForm.phone.trim(),
        note: contactForm.note.trim(),
      })
      setContactForm({ name: '', phone: '', note: '' })
      await loadContacts()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kontakt xato')
    } finally {
      setBusy(false)
    }
  }

  function addToCart(p: Product, qty = 1) {
    setCart((prev) => {
      const i = prev.findIndex((l) => l.product_id === p.id)
      if (i >= 0) {
        const next = [...prev]
        const line = next[i]
        const q = Math.min(p.stock, line.quantity + qty)
        next[i] = { ...line, quantity: q, stock: p.stock, price: p.price }
        return next
      }
      return [
        ...prev,
        {
          product_id: p.id,
          name: p.name,
          price: p.price,
          quantity: Math.min(qty, p.stock),
          stock: p.stock,
        },
      ]
    })
    setKassaMsg('')
  }

  function setCartQty(productId: number, quantity: number) {
    setCart((prev) =>
      prev
        .map((l) =>
          l.product_id === productId
            ? { ...l, quantity: Math.max(0, Math.min(l.stock, quantity)) }
            : l,
        )
        .filter((l) => l.quantity > 0),
    )
  }

  async function scanBarcode() {
    if (!auth || !kassaBarcode.trim()) return
    setBusy(true)
    try {
      const res = await api.productByBarcode(auth, kassaBarcode.trim())
      addToCart(res.product, 1)
      setKassaBarcode('')
      setKassaMsg(`${res.product.name} qo‘shildi`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Barkod topilmadi')
    } finally {
      setBusy(false)
    }
  }

  async function checkoutPos() {
    if (!auth || cart.length === 0) return
    const pay = kassaOnly ? 'cash' : kassaPay
    if (pay === 'debt' && !kassaCustomer.trim() && !kassaContactId) {
      setError('Qarz uchun mijoz ismi yoki kontakt tanlang')
      return
    }
    setBusy(true)
    setKassaMsg('')
    try {
      const res = await api.posSale(auth, {
        items: cart.map((l) => ({
          product_id: l.product_id,
          quantity: l.quantity,
        })),
        payment: pay,
        customer_name: kassaCustomer.trim() || undefined,
        phone: kassaPhone.trim() || undefined,
        promo_code: kassaPromo.trim() || undefined,
        contact_id: kassaContactId || undefined,
      })
      setCart([])
      setKassaPromo('')
      setKassaMsg(
        `Chek #${res.order.id} · ${money(res.total)} · ${
          res.payment === 'cash'
            ? 'Naqd'
            : res.payment === 'card'
              ? 'Karta'
              : `Qarz (qoldiq ${money(res.debt_balance || 0)})`
        }`,
      )
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sotuv xato')
    } finally {
      setBusy(false)
    }
  }

  async function loadDebts() {
    if (!auth) return
    try {
      const res = await api.debts(auth)
      setDebtors(res.debtors)
      setDebtTotals(res.totals)
      const c = await api.contacts(auth)
      setContacts(c.contacts)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Qarz xato')
    }
  }

  async function openDebtLedger(contactId: number) {
    if (!auth) return
    setBusy(true)
    try {
      const res = await api.debtLedger(auth, contactId)
      setDebtContactId(contactId)
      setDebtEntries(res.entries)
      setDebtBalance(res.balance)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Jurnal xato')
    } finally {
      setBusy(false)
    }
  }

  async function submitDebtEntry() {
    if (!auth || !debtContactId) return
    const amount = Number(debtForm.amount)
    if (!Number.isFinite(amount) || amount <= 0) {
      setError('Summa noto‘g‘ri')
      return
    }
    setBusy(true)
    try {
      const res = await api.addDebt(auth, {
        contact_id: debtContactId,
        amount,
        kind: debtForm.kind,
        note: debtForm.note.trim() || undefined,
      })
      setDebtForm({ amount: '', kind: 'payment', note: '' })
      setDebtBalance(res.balance)
      await openDebtLedger(debtContactId)
      await loadDebts()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Qarz yozuvi xato')
    } finally {
      setBusy(false)
    }
  }

  async function loadPromos() {
    if (!auth) return
    try {
      const res = await api.promos(auth)
      setPromos(res.promos)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Promo xato')
    }
  }

  async function savePromo() {
    if (!auth || !promoForm.code.trim()) return
    setBusy(true)
    try {
      await api.upsertPromo(auth, {
        code: promoForm.code.trim(),
        discount_percent: Number(promoForm.discount_percent) || 0,
        discount_amount: Number(promoForm.discount_amount) || 0,
        min_order: Number(promoForm.min_order) || 0,
        is_active: true,
      })
      setPromoForm({
        code: '',
        discount_percent: '10',
        discount_amount: '0',
        min_order: '0',
      })
      await loadPromos()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Promo saqlash xato')
    } finally {
      setBusy(false)
    }
  }

  async function loadReport() {
    if (!auth) return
    setBusy(true)
    try {
      const res = await api.reports(auth, reportFrom, reportTo)
      setReport(res.report)
      setDebtTotals(res.debts)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Hisobot xato')
    } finally {
      setBusy(false)
    }
  }

  async function loadCatalogCats() {
    if (!auth) return
    try {
      const res = await api.categories(auth)
      setCatalogCats(res.categories)
    } catch {
      /* ignore */
    }
  }

  async function createProduct() {
    if (!auth || !productForm.name.trim()) return
    const price = Number(productForm.price)
    if (!Number.isFinite(price) || price < 0) {
      setError('Narx noto‘g‘ri')
      return
    }
    setBusy(true)
    try {
      await api.createProduct(auth, {
        name: productForm.name.trim(),
        price,
        stock: Number(productForm.stock) || 0,
        barcode: productForm.barcode.trim() || undefined,
        description: productForm.description.trim() || undefined,
        category_id: productForm.category_id
          ? Number(productForm.category_id)
          : undefined,
      })
      setProductForm({
        name: '',
        price: '',
        stock: '0',
        barcode: '',
        category_id: '',
        description: '',
      })
      setShowProductForm(false)
      const cat = await api.products(auth)
      setCatalog(cat.products)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mahsulot yaratish xato')
    } finally {
      setBusy(false)
    }
  }

  async function addCategory() {
    if (!auth || !newCatName.trim()) return
    setBusy(true)
    try {
      await api.createCategory(auth, newCatName.trim())
      setNewCatName('')
      await loadCatalogCats()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Toifa xato')
    } finally {
      setBusy(false)
    }
  }

  async function markOrderDebt(orderId: number) {
    if (!auth) return
    if (!window.confirm(`#${orderId} qarzga yozilsinmi?`)) return
    setBusy(true)
    try {
      await api.markDebt(auth, orderId)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Qarz xato')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (!auth) return
    if (tab === 'debts') void loadDebts()
    if (tab === 'promos') void loadPromos()
    if (tab === 'reports') void loadReport()
    if (tab === 'products' || tab === 'kassa') {
      void loadCatalogCats()
      void loadContacts()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth, tab])

  function renderOrderCard(o: Order, showPay = false) {
    const open = openOrderId === o.id
    return (
      <article key={o.id} className="tx">
        <button
          type="button"
          className="tx-head"
          onClick={() => void toggleDetail(o.id)}
        >
          <div className="tx-left">
            <span className="tx-ico">📦</span>
            <div>
              <h3 className="tx-title">#{o.id}</h3>
              <p className="tx-sub">
                {o.phone || '—'} · {o.delivery_address || 'Manzil yo‘q'}
                {o.delivery_slot ? ` · ${o.delivery_slot}` : ''}
              </p>
              <div className="meta" style={{ marginTop: 6 }}>
                <span className="badge">{o.status_label}</span>
                <span className="badge warn">{o.payment_label}</span>
              </div>
            </div>
          </div>
          <div className="tx-right">
            <div className="tx-amount">{money(o.price)}</div>
            <div className="muted-sm" style={{ marginTop: 4 }}>
              {o.created_at}
            </div>
          </div>
        </button>

        {open ? (
          <div className="detail">
            {orderItems.length === 0 ? (
              <p className="muted-sm">Mahsulotlar yo‘q</p>
            ) : (
              <ul className="lines">
                {orderItems.map((it) => (
                  <li key={it.id}>
                    <span>
                      {it.product_name} × {it.quantity}
                    </span>
                    <span className="mono">{money(it.line_total)}</span>
                  </li>
                ))}
              </ul>
            )}
            {o.description ? <p className="note">{o.description}</p> : null}
          </div>
        ) : null}

        {showPay ? (
          <div className="actions">
            <button
              type="button"
              className="btn btn-ok"
              onClick={() => void changePayment(o.id, 'confirm')}
            >
              Tasdiqlash
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void changePayment(o.id, 'reject')}
            >
              Rad etish
            </button>
          </div>
        ) : (
          <div className="actions">
            {['accepted', 'in_delivery', 'delivered', 'cancelled'].map((st) => (
              <button
                key={st}
                type="button"
                className="btn btn-ghost"
                onClick={() => void changeStatus(o.id, st)}
              >
                {st === 'accepted'
                  ? 'Qabul'
                  : st === 'in_delivery'
                    ? 'Yo‘lda'
                    : st === 'delivered'
                      ? 'Yetkazildi'
                      : 'Bekor'}
              </button>
            ))}
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void removeOrder(o.id)}
            >
              O‘chirish
            </button>
            {o.payment_status !== 'debt' && o.payment_status !== 'paid' ? (
              <button
                type="button"
                className="btn btn-warn"
                onClick={() => void markOrderDebt(o.id)}
              >
                Qarzga
              </button>
            ) : null}
          </div>
        )}
      </article>
    )
  }

  if (booting) {
    return (
      <div className="login">
        <div className="login-box">
          <div className="login-mark" aria-hidden />
          <h1>
            Admin <span>POS</span>
          </h1>
          <p>Telegram orqali tekshirilmoqda…</p>
        </div>
      </div>
    )
  }

  if (!auth) {
    return (
      <div className="login">
        <div className="login-box">
          <div className="login-mark" aria-hidden />
          <h1>
            Admin <span>POS</span>
          </h1>
          {tgInit ? (
            <>
              <p>Telegram ichidasiz — bir bosishda kiring.</p>
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: '100%', marginBottom: 12 }}
                disabled={busy}
                onClick={() =>
                  void bootstrap({ mode: 'tg', initData: tgInit })
                }
              >
                Telegram orqali kirish
              </button>
            </>
          ) : (
            <>
              <p>
                Brauzerdan kirish: Telegram Admin ID va PIN yozing.
              </p>
              <div className="field">
                <label>Telegram Admin ID</label>
                <input
                  value={pinForm.adminId}
                  onChange={(e) =>
                    setPinForm((s) => ({ ...s, adminId: e.target.value }))
                  }
                  placeholder="123456789"
                  inputMode="numeric"
                />
              </div>
              <div className="field">
                <label>PIN</label>
                <input
                  type="password"
                  value={pinForm.pin}
                  onChange={(e) =>
                    setPinForm((s) => ({ ...s, pin: e.target.value }))
                  }
                  placeholder="••••"
                  autoComplete="current-password"
                />
              </div>
              {error ? <div className="error">{error}</div> : null}
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={busy}
                onClick={() =>
                  void bootstrap({
                    mode: 'pin',
                    pin: pinForm.pin,
                    adminId: Number(pinForm.adminId),
                  })
                }
              >
                PIN bilan kirish
              </button>
              <p className="muted-sm" style={{ marginTop: 12 }}>
                {tgReady
                  ? 'Yoki botdagi 🖥 Admin ilova tugmasini Telegram ichida bosing.'
                  : 'Telegram kutilyapti…'}
              </p>
            </>
          )}
          <button
            type="button"
            className="btn btn-ghost"
            style={{ width: '100%', marginTop: 10 }}
            onClick={() => setShowCode((v) => !v)}
          >
            {showCode ? 'Kodni yopish' : 'Botdagi bir martalik kod'}
          </button>
          {showCode ? (
            <>
              <p className="muted-sm" style={{ marginTop: 12 }}>
                Botda <b>🔑 Kirish kodi</b> oling, keyin shu yerga yozing.
              </p>
              <div className="field">
                <label>Telegram Admin ID</label>
                <input
                  value={pinForm.adminId}
                  onChange={(e) =>
                    setPinForm((s) => ({ ...s, adminId: e.target.value }))
                  }
                  placeholder="123456789"
                  inputMode="numeric"
                />
              </div>
              <div className="field">
                <label>Kirish kodi (botdan)</label>
                <input
                  value={pinForm.code}
                  onChange={(e) =>
                    setPinForm((s) => ({ ...s, code: e.target.value }))
                  }
                  placeholder="123456"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={busy}
                onClick={() => void loginWithCode()}
              >
                Kod bilan kirish
              </button>
            </>
          ) : null}
          {tgInit && error ? <div className="error">{error}</div> : null}
        </div>
      </div>
    )
  }

  return (
    <div className={`app${busy ? ' busy' : ''}`}>
      <header className="pos-top">
        <button
          type="button"
          className="pos-brand"
          onClick={() => setMenuOpen(true)}
        >
          <span className="pos-logo">{initials}</span>
          <div>
            <strong>{shop}</strong>
            <span>
              Zifra POS · {lastSync ? lastSync : 'online'}
            </span>
          </div>
        </button>
        <div className="pos-top-actions">
          <button
            type="button"
            className="pos-ico"
            title="Yangilash"
            onClick={() => void refreshAll()}
          >
            ↻
          </button>
          <button
            type="button"
            className="pos-ico"
            title="Yangi buyurtmalar"
            onClick={() => {
              setOrderStatus('new')
              setTab('orders')
            }}
          >
            🔔
            {stats && stats.stats.new_orders > 0 ? (
              <span className="dot" />
            ) : null}
          </button>
        </div>
      </header>

      {error ? <div className="error">{error}</div> : null}

      {tab === 'dash' && stats ? (
        <>
          <div className="pos-kpis">
            <button
              type="button"
              className="pos-kpi primary"
              onClick={() => setTab('orders')}
            >
              <span className="lab">Bugungi savdo</span>
              <span className="val">{money(stats.daily.revenue)}</span>
              <span className="sub">{stats.daily.orders_count} buyurtma</span>
            </button>
            <button
              type="button"
              className="pos-kpi danger"
              onClick={() => {
                setOrderStatus('new')
                setTab('orders')
              }}
            >
              <span className="lab">Yangi</span>
              <span className="val">{stats.stats.new_orders}</span>
              <span className="sub">Kutilayotgan</span>
            </button>
            <button
              type="button"
              className="pos-kpi warn"
              onClick={() => setTab('payments')}
            >
              <span className="lab">To‘lov</span>
              <span className="val">{stats.payments_waiting}</span>
              <span className="sub">{money(stats.daily.waiting_sum)}</span>
            </button>
            <button
              type="button"
              className="pos-kpi ok"
              onClick={() => {
                setLowOnly(true)
                setTab('warehouse')
              }}
            >
              <span className="lab">Kam qoldiq</span>
              <span className="val">{stats.warehouse.low_stock}</span>
              <span className="sub">
                {stats.warehouse.units.toLocaleString()} dona
              </span>
            </button>
          </div>

          <div className="pos-sec">
            <h2>Modullar</h2>
            <button
              type="button"
              className="pos-link"
              onClick={() => setMenuOpen(true)}
            >
              Barchasi
            </button>
          </div>
          <div className="pos-modules">
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('kassa')}
            >
              <span className="pos-mod-ico blue">🖥</span>
              <strong>Kassa</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('orders')}
            >
              {stats.stats.new_orders > 0 ? (
                <span className="badge">{stats.stats.new_orders}</span>
              ) : null}
              <span className="pos-mod-ico blue">📦</span>
              <strong>Buyurtmalar</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('payments')}
            >
              {stats.payments_waiting > 0 ? (
                <span className="badge">{stats.payments_waiting}</span>
              ) : null}
              <span className="pos-mod-ico amber">💳</span>
              <strong>To‘lovlar</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('warehouse')}
            >
              <span className="pos-mod-ico green">🏭</span>
              <strong>Ombor</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('products')}
            >
              <span className="pos-mod-ico lav">🏷</span>
              <strong>Tovarlar</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('debts')}
            >
              <span className="pos-mod-ico red">📒</span>
              <strong>Qarz</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('reports')}
            >
              <span className="pos-mod-ico green">📊</span>
              <strong>Hisobot</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => setTab('promos')}
            >
              <span className="pos-mod-ico amber">🏷</span>
              <strong>Promo</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => {
                setMorePanel('broadcast')
                setTab('more')
              }}
            >
              <span className="pos-mod-ico blue">📣</span>
              <strong>Xabar</strong>
            </button>
            <button
              type="button"
              className="pos-mod"
              onClick={() => {
                setMorePanel('contacts')
                setTab('more')
              }}
            >
              <span className="pos-mod-ico red">👤</span>
              <strong>Mijozlar</strong>
            </button>
          </div>

          <div className="pos-sec">
            <h2>Bugungi top</h2>
            <button
              type="button"
              className="pos-link"
              onClick={() => setTab('products')}
            >
              Tovarlar
            </button>
          </div>
          <div className="list">
            {stats.daily.top?.length ? (
              stats.daily.top.map((t) => (
                <div key={t.product_name} className="tx">
                  <div className="tx-head" style={{ cursor: 'default' }}>
                    <div className="tx-left">
                      <span className="tx-ico">🛒</span>
                      <div>
                        <h3 className="tx-title">{t.product_name}</h3>
                        <p className="tx-sub">Sotuv</p>
                      </div>
                    </div>
                    <div className="tx-right">
                      <div className="tx-amount plus">+{t.qty}</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty">Bugun hali savdo yo‘q</div>
            )}
          </div>

          <section className="section" style={{ marginTop: 14 }}>
            <div className="grid">
              <div className="card">
                <div className="label">To‘langan</div>
                <div className="value accent">{money(stats.daily.paid_sum)}</div>
              </div>
              <div className="card">
                <div className="label">Ombor kirim/chiqim</div>
                <div className="value">
                  +{stats.warehouse.today_in} / −{stats.warehouse.today_out}
                </div>
              </div>
            </div>
          </section>
        </>
      ) : null}

      {tab === 'kassa' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Kassa</h1>
              <p>Do‘kon sotuvi · naqd / karta / qarz</p>
            </div>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setCart([])}
            >
              Tozalash
            </button>
          </div>

          <div className="field">
            <label>Barkod / shtrix-kod</label>
            <div className="actions" style={{ marginTop: 0 }}>
              <input
                value={kassaBarcode}
                onChange={(e) => setKassaBarcode(e.target.value)}
                placeholder="Kodni skanerlang yoki yozing"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void scanBarcode()
                }}
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void scanBarcode()}
              >
                Qo‘shish
              </button>
            </div>
          </div>

          <div className="field">
            <label>Mahsulot qidirish</label>
            <input
              value={kassaSearch}
              onChange={(e) => setKassaSearch(e.target.value)}
              placeholder="Nom yoki ID..."
            />
          </div>

          <div className="list kassa-products">
            {kassaFiltered.map((p) => (
              <button
                key={p.id}
                type="button"
                className="item kassa-pick"
                onClick={() => addToCart(p)}
              >
                <div className="row-between">
                  <h3>{p.name}</h3>
                  <span className="mono">{money(p.price)}</span>
                </div>
                <p>
                  Omborda {p.stock}
                  {p.barcode ? ` · ${p.barcode}` : ''}
                </p>
              </button>
            ))}
            {kassaFiltered.length === 0 ? (
              <div className="empty">Mahsulot topilmadi</div>
            ) : null}
          </div>

          <div className="pos-sec" style={{ marginTop: 16 }}>
            <h2>Savatcha</h2>
            <span className="pos-link">{money(cartTotal)}</span>
          </div>
          <div className="list">
            {cart.length === 0 ? (
              <div className="empty">Savatcha bo‘sh</div>
            ) : (
              cart.map((l) => (
                <div key={l.product_id} className="item">
                  <div className="row-between">
                    <h3>{l.name}</h3>
                    <span className="mono">{money(l.price * l.quantity)}</span>
                  </div>
                  <div className="actions">
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => setCartQty(l.product_id, l.quantity - 1)}
                    >
                      −
                    </button>
                    <span className="mono">{l.quantity}</span>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => setCartQty(l.product_id, l.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="card" style={{ marginTop: 12 }}>
            {kassaOnly ? (
              <p className="muted-sm" style={{ marginBottom: 10 }}>
                To‘lov: faqat <b>Naqd</b>
              </p>
            ) : (
              <div className="tabs-inline">
                {(
                  [
                    ['cash', 'Naqd'],
                    ['card', 'Karta'],
                    ['debt', 'Qarz'],
                  ] as const
                ).map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={`chip${kassaPay === id ? ' active' : ''}`}
                    onClick={() => setKassaPay(id)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
            <div className="field">
              <label>Promo kod</label>
              <input
                value={kassaPromo}
                onChange={(e) => setKassaPromo(e.target.value)}
                placeholder="BARAKA10"
              />
            </div>
            {!kassaOnly && kassaPay === 'debt' ? (
              <>
                <div className="field">
                  <label>Mijoz (kontakt)</label>
                  <select
                    value={kassaContactId || ''}
                    onChange={(e) =>
                      setKassaContactId(Number(e.target.value) || 0)
                    }
                  >
                    <option value="">Yangi mijoz…</option>
                    {contacts.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                        {c.balance ? ` (${money(c.balance)})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Ism</label>
                  <input
                    value={kassaCustomer}
                    onChange={(e) => setKassaCustomer(e.target.value)}
                    placeholder="Mijoz ismi"
                  />
                </div>
                <div className="field">
                  <label>Telefon</label>
                  <input
                    value={kassaPhone}
                    onChange={(e) => setKassaPhone(e.target.value)}
                    placeholder="+998..."
                  />
                </div>
              </>
            ) : null}
            {kassaMsg ? <p className="muted-sm ok-text">{kassaMsg}</p> : null}
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={busy || cart.length === 0}
              onClick={() => void checkoutPos()}
            >
              Sotish · {money(cartTotal)}
            </button>
          </div>
        </section>
      ) : null}

      {tab === 'debts' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Qarzdorlar</h1>
              <p>Qarz berish va undirish</p>
            </div>
          </div>
          <div className="grid">
            <div className="card">
              <div className="label">Ochiq qarz</div>
              <div className="value accent">{money(debtTotals.open)}</div>
            </div>
            <div className="card">
              <div className="label">Jami berilgan</div>
              <div className="value">{money(debtTotals.debts)}</div>
            </div>
          </div>

          {debtContactId ? (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="row-between">
                <h3>Jurnal · balans {money(debtBalance)}</h3>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setDebtContactId(null)
                    setDebtEntries([])
                  }}
                >
                  Orqaga
                </button>
              </div>
              <div className="field">
                <label>Amaliyot</label>
                <select
                  value={debtForm.kind}
                  onChange={(e) =>
                    setDebtForm((s) => ({
                      ...s,
                      kind: e.target.value as 'debt' | 'payment',
                    }))
                  }
                >
                  <option value="payment">To‘lov (undirish)</option>
                  <option value="debt">Qo‘shimcha qarz</option>
                </select>
              </div>
              <div className="field">
                <label>Summa</label>
                <input
                  value={debtForm.amount}
                  onChange={(e) =>
                    setDebtForm((s) => ({ ...s, amount: e.target.value }))
                  }
                  inputMode="numeric"
                  placeholder="100000"
                />
              </div>
              <div className="field">
                <label>Izoh</label>
                <input
                  value={debtForm.note}
                  onChange={(e) =>
                    setDebtForm((s) => ({ ...s, note: e.target.value }))
                  }
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void submitDebtEntry()}
              >
                Saqlash
              </button>
              <div className="list" style={{ marginTop: 12 }}>
                {debtEntries.map((e) => (
                  <div key={e.id} className="item">
                    <div className="row-between">
                      <h3>{e.kind === 'debt' ? 'Qarz' : 'To‘lov'}</h3>
                      <span
                        className={`mono ${e.kind === 'debt' ? 'danger-text' : 'ok-text'}`}
                      >
                        {e.kind === 'debt' ? '+' : '−'}
                        {money(e.amount)}
                      </span>
                    </div>
                    <p>
                      {e.created_at}
                      {e.note ? ` · ${e.note}` : ''}
                      {e.order_id ? ` · #${e.order_id}` : ''}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="list" style={{ marginTop: 12 }}>
              {debtors.length === 0 ? (
                <div className="empty">Qarzdor yo‘q</div>
              ) : (
                debtors.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className="item kassa-pick"
                    onClick={() => void openDebtLedger(d.id)}
                  >
                    <div className="row-between">
                      <h3>{d.name}</h3>
                      <span className="mono danger-text">
                        {money(d.balance || 0)}
                      </span>
                    </div>
                    <p>{d.phone || 'Telefon yo‘q'}</p>
                  </button>
                ))
              )}
            </div>
          )}
        </section>
      ) : null}

      {tab === 'reports' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Hisobot</h1>
              <p>Savdo, P&L taxminiy, ABC</p>
            </div>
          </div>
          <div className="actions" style={{ marginTop: 0 }}>
            <div className="field" style={{ flex: 1, margin: 0 }}>
              <label>Dan</label>
              <input
                type="date"
                value={reportFrom}
                onChange={(e) => setReportFrom(e.target.value)}
              />
            </div>
            <div className="field" style={{ flex: 1, margin: 0 }}>
              <label>Gacha</label>
              <input
                type="date"
                value={reportTo}
                onChange={(e) => setReportTo(e.target.value)}
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void loadReport()}
            >
              Yuklash
            </button>
          </div>
          {report ? (
            <>
              <div className="grid" style={{ marginTop: 12 }}>
                <div className="card">
                  <div className="label">Savdo</div>
                  <div className="value accent">{money(report.orders_sum)}</div>
                  <p className="muted-sm">{report.orders_count} buyurtma</p>
                </div>
                <div className="card">
                  <div className="label">To‘langan</div>
                  <div className="value">{money(report.paid_sum)}</div>
                </div>
                <div className="card">
                  <div className="label">Qarz savdo</div>
                  <div className="value">{money(report.debt_sum)}</div>
                </div>
                <div className="card">
                  <div className="label">P&L (taxminiy)</div>
                  <div className="value">{money(report.profit_approx)}</div>
                </div>
              </div>
              <div className="pos-sec">
                <h2>ABC tahlil</h2>
              </div>
              <div className="list">
                {report.abc.length === 0 ? (
                  <div className="empty">Ma’lumot yo‘q</div>
                ) : (
                  report.abc.map((r) => (
                    <div key={r.product_name} className="item">
                      <div className="row-between">
                        <h3>
                          <span className="badge">{r.grade}</span> {r.product_name}
                        </h3>
                        <span className="mono">{money(r.revenue)}</span>
                      </div>
                      <p>{r.qty} dona</p>
                    </div>
                  ))
                )}
              </div>
              <div className="pos-sec">
                <h2>Kunlik</h2>
              </div>
              <div className="list">
                {report.by_day.map((d) => (
                  <div key={d.date} className="item">
                    <div className="row-between">
                      <h3>{d.date}</h3>
                      <span className="mono">{money(d.revenue)}</span>
                    </div>
                    <p>{d.orders_count} buyurtma</p>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </section>
      ) : null}

      {tab === 'promos' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Promo kodlar</h1>
              <p>Chegirma va aksiya</p>
            </div>
          </div>
          <div className="card">
            <div className="field">
              <label>Kod</label>
              <input
                value={promoForm.code}
                onChange={(e) =>
                  setPromoForm((s) => ({ ...s, code: e.target.value }))
                }
                placeholder="BARAKA10"
              />
            </div>
            <div className="field">
              <label>Foiz (%)</label>
              <input
                value={promoForm.discount_percent}
                onChange={(e) =>
                  setPromoForm((s) => ({
                    ...s,
                    discount_percent: e.target.value,
                  }))
                }
                inputMode="numeric"
              />
            </div>
            <div className="field">
              <label>Summa chegirma</label>
              <input
                value={promoForm.discount_amount}
                onChange={(e) =>
                  setPromoForm((s) => ({
                    ...s,
                    discount_amount: e.target.value,
                  }))
                }
                inputMode="numeric"
              />
            </div>
            <div className="field">
              <label>Minimal buyurtma</label>
              <input
                value={promoForm.min_order}
                onChange={(e) =>
                  setPromoForm((s) => ({ ...s, min_order: e.target.value }))
                }
                inputMode="numeric"
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void savePromo()}
            >
              Saqlash
            </button>
          </div>
          <div className="list" style={{ marginTop: 12 }}>
            {promos.map((p) => (
              <div key={p.code} className="item">
                <div className="row-between">
                  <h3>{p.code}</h3>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => {
                      if (!auth) return
                      void api
                        .patchPromo(auth, p.code, { is_active: !p.is_active })
                        .then(() => loadPromos())
                    }}
                  >
                    {p.is_active ? 'O‘chirish' : 'Yoqish'}
                  </button>
                </div>
                <p>
                  {p.discount_percent
                    ? `−${p.discount_percent}%`
                    : `−${money(p.discount_amount)}`}
                  {p.min_order ? ` · min ${money(p.min_order)}` : ''}
                  {!p.is_active ? ' · nofaol' : ''}
                </p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {tab === 'orders' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Buyurtmalar</h1>
              <p>Status va tafsilotlarni boshqaring</p>
            </div>
          </div>
          <div className="field">
            <label>Qidiruv (ID / telefon)</label>
            <input
              value={orderQuery}
              onChange={(e) => setOrderQuery(e.target.value)}
              placeholder="masalan 102 yoki 90..."
            />
          </div>
          <div className="tabs-inline">
            {ORDER_FILTERS.map(([k, label]) => (
              <button
                key={k}
                type="button"
                className={`chip${orderStatus === k ? ' active' : ''}`}
                onClick={() => setOrderStatus(k)}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="list">
            {orders.length === 0 ? (
              <div className="empty">Buyurtma yo‘q</div>
            ) : (
              orders.map((o) => renderOrderCard(o))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'payments' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>To‘lovlar</h1>
              <p>Karta orqali kutayotgan to‘lovlar</p>
            </div>
          </div>
          <div className="list">
            {payments.length === 0 ? (
              <div className="empty">Kutayotgan to‘lov yo‘q</div>
            ) : (
              payments.map((o) => renderOrderCard(o, true))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'warehouse' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Ombor</h1>
              <p>Kirim, chiqim va qoldiq</p>
            </div>
            <button
              type="button"
              className={`chip${lowOnly ? ' active' : ''}`}
              onClick={() => setLowOnly((v) => !v)}
            >
              Kam qoldiq
            </button>
          </div>
          <div className="card" style={{ marginBottom: 12 }}>
            <div className="field">
              <label>Amal</label>
              <select
                value={stockForm.mode}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, mode: e.target.value }))
                }
              >
                <option value="in">📥 Kirim</option>
                <option value="out">📤 Chiqim</option>
                <option value="inventory">📋 Inventar</option>
              </select>
            </div>
            <div className="field">
              <label>Mahsulot</label>
              <select
                value={stockForm.product_id || ''}
                onChange={(e) =>
                  setStockForm((s) => ({
                    ...s,
                    product_id: Number(e.target.value),
                  }))
                }
              >
                <option value="">Tanlang</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.category_name} · {p.name} ({p.stock})
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Miqdor</label>
              <input
                type="number"
                min={0}
                value={stockForm.qty}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, qty: Number(e.target.value) }))
                }
              />
            </div>
            <div className="field">
              <label>Izoh</label>
              <input
                value={stockForm.note}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, note: e.target.value }))
                }
                placeholder="ixtiyoriy"
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void submitStock()}
            >
              Saqlash
            </button>
          </div>

          <div className="tabs-inline">
            <button
              type="button"
              className={`chip${selectedCat === 'all' ? ' active' : ''}`}
              onClick={() => setSelectedCat('all')}
            >
              Hammasi
            </button>
            {categories.map((c) => (
              <button
                key={c.category_id}
                type="button"
                className={`chip${selectedCat === c.category_id ? ' active' : ''}`}
                onClick={() => setSelectedCat(c.category_id)}
              >
                {c.category_name}
                {c.low_count ? ` · ${c.low_count}` : ''}
              </button>
            ))}
          </div>
          <div className="list">
            {filteredProducts.map((p) => (
              <div key={p.id} className="item">
                <div className="row-between">
                  <div>
                    <h3>{p.name}</h3>
                    <p>
                      {p.category_name} · {money(p.price)}
                    </p>
                  </div>
                  <div className="mono value" style={{ fontSize: '1.1rem' }}>
                    {p.stock}
                  </div>
                </div>
                <div className="actions">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void quickIn(p.id, 1)}
                  >
                    +1
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void quickIn(p.id, 10)}
                  >
                    +10
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() =>
                      setStockForm({
                        product_id: p.id,
                        mode: 'in',
                        qty: 1,
                        note: '',
                      })
                    }
                  >
                    Forma
                  </button>
                </div>
              </div>
            ))}
            {filteredProducts.length === 0 ? (
              <div className="empty">Mahsulot yo‘q</div>
            ) : null}
          </div>
        </section>
      ) : null}

      {tab === 'more' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Ko‘proq</h1>
              <p>Broadcast, kontakt, CSV, jurnal</p>
            </div>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => {
                void api.logout(auth)
                clearAuth()
                setAuth(null)
              }}
            >
              Chiqish
            </button>
          </div>
          <div className="tabs-inline">
            {(
              [
                ['broadcast', 'Broadcast'],
                ['contacts', 'Kontaktlar'],
                ['csv', 'CSV'],
                ['moves', 'Jurnal'],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`chip${morePanel === id ? ' active' : ''}`}
                onClick={() => setMorePanel(id)}
              >
                {label}
              </button>
            ))}
          </div>

          {morePanel === 'broadcast' ? (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="field">
                <label>Barcha mijozlarga xabar</label>
                <textarea
                  className="textarea"
                  rows={5}
                  value={broadcastText}
                  onChange={(e) => setBroadcastText(e.target.value)}
                  placeholder="Aksiya, yangilik yoki e’lon matni..."
                />
              </div>
              {broadcastResult ? (
                <p className="muted-sm">{broadcastResult}</p>
              ) : null}
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void sendBroadcast()}
              >
                Yuborish
              </button>
            </div>
          ) : null}

          {morePanel === 'contacts' ? (
            <>
              <div className="card" style={{ marginTop: 12 }}>
                <div className="field">
                  <label>Ism</label>
                  <input
                    value={contactForm.name}
                    onChange={(e) =>
                      setContactForm((s) => ({ ...s, name: e.target.value }))
                    }
                    placeholder="Mijoz ismi"
                  />
                </div>
                <div className="field">
                  <label>Telefon</label>
                  <input
                    value={contactForm.phone}
                    onChange={(e) =>
                      setContactForm((s) => ({ ...s, phone: e.target.value }))
                    }
                    placeholder="+998..."
                  />
                </div>
                <div className="field">
                  <label>Izoh</label>
                  <input
                    value={contactForm.note}
                    onChange={(e) =>
                      setContactForm((s) => ({ ...s, note: e.target.value }))
                    }
                    placeholder="ixtiyoriy"
                  />
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void addContact()}
                >
                  Qo‘shish
                </button>
              </div>
              <div className="list" style={{ marginTop: 12 }}>
                {contacts.length === 0 ? (
                  <div className="empty">Kontakt yo‘q</div>
                ) : (
                  contacts.map((c) => (
                    <div key={c.id} className="item">
                      <h3>{c.name}</h3>
                      <p>
                        {c.phone || 'Telefon yo‘q'}
                        {c.note ? ` · ${c.note}` : ''}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : null}

          {morePanel === 'csv' ? (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="actions" style={{ marginTop: 0 }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void downloadCsv()}
                >
                  CSV yuklab olish
                </button>
                <label className="btn btn-ghost file-btn">
                  Fayl tanlash
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    hidden
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      const reader = new FileReader()
                      reader.onload = () => {
                        setCsvText(String(reader.result || ''))
                        setCsvInfo(`Tanlandi: ${file.name}`)
                      }
                      reader.readAsText(file)
                    }}
                  />
                </label>
              </div>
              <div className="field" style={{ marginTop: 12 }}>
                <label>CSV matn</label>
                <textarea
                  className="textarea"
                  rows={8}
                  value={csvText}
                  onChange={(e) => setCsvText(e.target.value)}
                  placeholder="id,name,price,..."
                />
              </div>
              {csvInfo ? <p className="muted-sm">{csvInfo}</p> : null}
              <button
                type="button"
                className="btn btn-warn"
                onClick={() => void uploadCsv()}
              >
                Import qilish
              </button>
            </div>
          ) : null}

          {morePanel === 'moves' ? (
            <div className="list" style={{ marginTop: 12 }}>
              {moves.length === 0 ? (
                <div className="empty">Harakat yo‘q</div>
              ) : (
                moves.map((m) => (
                  <div key={m.id} className="item">
                    <div className="row-between">
                      <h3>{m.product_name}</h3>
                      <span className="badge">
                        {REASON[m.reason] || m.reason}
                      </span>
                    </div>
                    <p className="mono">
                      {m.delta > 0 ? `+${m.delta}` : m.delta} → {m.stock_after}
                      {m.note ? ` · ${m.note}` : ''}
                    </p>
                    <p>{m.created_at}</p>
                  </div>
                ))
              )}
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === 'products' ? (
        <section className="section">
          <div className="page-h">
            <div>
              <h1>Mahsulotlar</h1>
              <p>Yaratish, narx va faollik</p>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowProductForm((v) => !v)}
            >
              {showProductForm ? 'Yopish' : '+ Yangi'}
            </button>
          </div>

          {showProductForm ? (
            <div className="card" style={{ marginBottom: 12 }}>
              <div className="field">
                <label>Nom</label>
                <input
                  value={productForm.name}
                  onChange={(e) =>
                    setProductForm((s) => ({ ...s, name: e.target.value }))
                  }
                  placeholder="Mahsulot nomi"
                />
              </div>
              <div className="field">
                <label>Narx</label>
                <input
                  value={productForm.price}
                  onChange={(e) =>
                    setProductForm((s) => ({ ...s, price: e.target.value }))
                  }
                  inputMode="numeric"
                />
              </div>
              <div className="field">
                <label>Boshlang‘ich qoldiq</label>
                <input
                  value={productForm.stock}
                  onChange={(e) =>
                    setProductForm((s) => ({ ...s, stock: e.target.value }))
                  }
                  inputMode="numeric"
                />
              </div>
              <div className="field">
                <label>Barkod</label>
                <input
                  value={productForm.barcode}
                  onChange={(e) =>
                    setProductForm((s) => ({ ...s, barcode: e.target.value }))
                  }
                />
              </div>
              <div className="field">
                <label>Toifa</label>
                <select
                  value={productForm.category_id}
                  onChange={(e) =>
                    setProductForm((s) => ({
                      ...s,
                      category_id: e.target.value,
                    }))
                  }
                >
                  <option value="">Tanlanmagan</option>
                  {catalogCats.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="actions" style={{ marginTop: 0 }}>
                <input
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  placeholder="Yangi toifa"
                />
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => void addCategory()}
                >
                  Toifa +
                </button>
              </div>
              <div className="field">
                <label>Izoh</label>
                <input
                  value={productForm.description}
                  onChange={(e) =>
                    setProductForm((s) => ({
                      ...s,
                      description: e.target.value,
                    }))
                  }
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void createProduct()}
              >
                Saqlash
              </button>
            </div>
          ) : null}
          <div className="list">
            {catalog.map((p) => (
              <div key={p.id} className="item">
                <div className="row-between">
                  <div>
                    <h3>
                      {p.is_active ? '✅' : '🚫'} {p.name}
                    </h3>
                    <p>
                      {p.category_name} · {p.stock} dona
                    </p>
                  </div>
                  <div className="mono">{money(p.price)}</div>
                </div>
                <div className="actions">
                  <input
                    className="price-input"
                    type="number"
                    min={0}
                    value={priceEdit[p.id] ?? String(p.price)}
                    onChange={(e) =>
                      setPriceEdit((s) => ({ ...s, [p.id]: e.target.value }))
                    }
                  />
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void savePrice(p)}
                  >
                    Narx
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void toggleProduct(p)}
                  >
                    {p.is_active ? 'Yashirish' : 'Ko‘rsatish'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {menuOpen ? (
        <>
          <button
            type="button"
            className="menu-backdrop"
            aria-label="Yopish"
            onClick={() => setMenuOpen(false)}
          />
          <div className="menu-sheet" role="dialog">
            <div className="menu-handle" />
            <h3>POS menyu</h3>
            <div className="menu-grid">
              {(
                (
                  kassaOnly
                    ? ([
                        ['kassa', '🖥', 'Kassa'],
                        ['products', '🛍', 'Tovar'],
                        ['warehouse', '🏭', 'Ombor'],
                      ] as const)
                    : ([
                        ['dash', '🏠', 'Asosiy'],
                        ['kassa', '🖥', 'Kassa'],
                        ['orders', '📦', 'Buyurtma'],
                        ['payments', '💳', 'To‘lov'],
                        ['warehouse', '🏭', 'Ombor'],
                        ['products', '🛍', 'Tovar'],
                        ['debts', '📒', 'Qarz'],
                        ['reports', '📊', 'Hisobot'],
                        ['promos', '🏷', 'Promo'],
                        ['more', '⋯', 'Ko‘proq'],
                      ] as const)
                )
              ).map(([id, ico, label]) => (
                <button
                  key={id}
                  type="button"
                  className="menu-item"
                  onClick={() => {
                    setTab(id)
                    setMenuOpen(false)
                  }}
                >
                  <span className="mi">{ico}</span>
                  <span>{label}</span>
                </button>
              ))}
              <button
                type="button"
                className="menu-item"
                onClick={() => {
                  void api.logout(auth)
                  clearAuth()
                  setAuth(null)
                  setMenuOpen(false)
                }}
              >
                <span className="mi">⎋</span>
                <span>Chiqish</span>
              </button>
            </div>
          </div>
        </>
      ) : null}

      <nav className="nav" aria-label="Admin menyu">
        <div className="nav-inner">
          {kassaOnly ? (
            <>
              <button
                type="button"
                className={`nav-btn${tab === 'products' ? ' active' : ''}`}
                onClick={() => setTab('products')}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 7h16v12H4z" />
                  <path d="M8 7V5a4 4 0 0 1 8 0v2" />
                </svg>
                Tovar
              </button>
              <div className="nav-center-wrap">
                <button
                  type="button"
                  className={`nav-center${tab === 'kassa' ? ' active' : ''}`}
                  aria-label="Kassa"
                  onClick={() => setTab('kassa')}
                >
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="14" rx="2" />
                    <path d="M7 18v2M17 18v2M8 10h8M8 13h5" />
                  </svg>
                </button>
              </div>
              <button
                type="button"
                className={`nav-btn${tab === 'warehouse' ? ' active' : ''}`}
                onClick={() => setTab('warehouse')}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 20V9l8-5 8 5v11" />
                  <path d="M9 20v-6h6v6" />
                </svg>
                Ombor
              </button>
            </>
          ) : (
            <>
          <button
            type="button"
            className={`nav-btn${tab === 'dash' ? ' active' : ''}`}
            onClick={() => setTab('dash')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z" />
            </svg>
            Asosiy
          </button>
          <button
            type="button"
            className={`nav-btn${tab === 'orders' ? ' active' : ''}`}
            onClick={() => setTab('orders')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 7h16v12H4z" />
              <path d="M8 7V5a4 4 0 0 1 8 0v2" />
            </svg>
            Buyurtma
          </button>
          <div className="nav-center-wrap">
            <button
              type="button"
              className={`nav-center${tab === 'kassa' ? ' active' : ''}`}
              aria-label="Kassa"
              onClick={() => setTab('kassa')}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="14" rx="2" />
                <path d="M7 18v2M17 18v2M8 10h8M8 13h5" />
              </svg>
            </button>
          </div>
          <button
            type="button"
            className={`nav-btn${tab === 'debts' ? ' active' : ''}`}
            onClick={() => setTab('debts')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 4h12v16H6z" />
              <path d="M9 8h6M9 12h6M9 16h4" />
            </svg>
            Qarz
          </button>
          <button
            type="button"
            className={`nav-btn${tab === 'warehouse' ? ' active' : ''}`}
            onClick={() => setTab('warehouse')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 20V9l8-5 8 5v11" />
              <path d="M9 20v-6h6v6" />
            </svg>
            Ombor
          </button>
            </>
          )}
        </div>
      </nav>
    </div>
  )
}
