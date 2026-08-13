export type Tab =
  | 'dash'
  | 'kassa'
  | 'orders'
  | 'payments'
  | 'warehouse'
  | 'products'
  | 'reports'
  | 'promos'
  | 'more'

export type MorePanel = 'moves' | 'broadcast' | 'csv' | 'contacts'

export type Order = {
  id: number
  user_id: number
  status: string
  status_label: string
  payment_status: string
  payment_label: string
  price: number
  phone: string
  delivery_address: string
  description: string
  delivery_slot: string
  created_at: string
  text: string
}

export type OrderItem = {
  id: number
  product_id: number | null
  product_name: string
  price: number
  quantity: number
  line_total: number
}

export type Product = {
  id: number
  name: string
  price: number
  stock: number
  category_id: number
  category_name: string
  is_active: boolean
  barcode?: string
  description?: string
}

export type Category = {
  category_id: number
  category_name: string
  emoji?: string
  product_count: number
  low_count: number
  stock_sum: number
}

export type CatalogCategory = {
  id: number
  name: string
  emoji?: string
  is_active: boolean
}

export type Movement = {
  id: number
  product_id: number
  product_name: string
  delta: number
  stock_after: number
  reason: string
  note: string
  order_id: number | null
  admin_id: number | null
  created_at: string
}

export type Contact = {
  id: number
  name: string
  phone: string
  note: string
  telegram_user_id: number | null
  balance?: number
  created_at: string
  updated_at: string
}

export type Promo = {
  code: string
  discount_percent: number
  discount_amount: number
  min_order: number
  is_active: boolean
}

export type CartLine = {
  product_id: number
  name: string
  price: number
  quantity: number
  stock: number
}

export type RangeReport = {
  date_from: string
  date_to: string
  orders_count: number
  orders_sum: number
  paid_count: number
  paid_sum: number
  debt_count: number
  debt_sum: number
  cancelled_count: number
  cancelled_sum: number
  profit_approx: number
  by_day: { date: string; orders_count: number; revenue: number }[]
  top: {
    product_name: string
    qty: number
    revenue: number
    grade: string
  }[]
  abc: {
    product_name: string
    qty: number
    revenue: number
    grade: string
  }[]
}

export type StatsPayload = {
  stats: {
    total_users: number
    total_orders: number
    new_orders: number
    active_orders: number
    delivered_orders: number
    revenue_sum: number
    today_orders: number
    today_sum: number
  }
  warehouse: {
    products: number
    units: number
    zero_stock: number
    low_stock: number
    today_in: number
    today_out: number
    today_moves: number
  }
  daily: {
    orders_count: number
    revenue: number
    date: string
    paid_count: number
    paid_sum: number
    waiting_count: number
    waiting_sum: number
    top: { product_name: string; qty: number }[]
  }
  payments_waiting: number
  low_stock_threshold: number
}
