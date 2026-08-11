export type Tab =
  | 'dash'
  | 'orders'
  | 'payments'
  | 'warehouse'
  | 'moves'
  | 'products'

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
}

export type Category = {
  category_id: number
  category_name: string
  product_count: number
  low_count: number
  stock_sum: number
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
