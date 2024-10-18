import MetaTrader5 as mt5
import time

# Inicializimi i MT5
if not mt5.initialize():
    print("MetaTrader5 initialization failed")
    mt5.shutdown()

# Parametrat e fitimit dhe humbjes së synuar
TARGET_PROFIT = 50.0  # Vendosni fitimin e synuar në dollarë
TARGET_LOSS = 50.0    # Vendosni humbjen e synuar në dollarë

def close_order(order):
    price = mt5.symbol_info_tick(order.symbol).bid if order.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(order.symbol).ask
    result = mt5.order_send(
        {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order.symbol,
            "volume": order.volume,
            "type": mt5.ORDER_TYPE_SELL if order.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": order.ticket,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "Closing order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
    )
    return result

last_notification_time = time.time()  # Koha e fundit e njoftimit

while True:
    # Merr të gjitha urdhrat e hapur
    orders = mt5.positions_get()
    if orders is None:
        print("No orders found")
    else:
        # Kontrolloni nëse ka kaluar 60 sekonda për të njoftuar
        current_time = time.time()
        if current_time - last_notification_time >= 60:
            print(f"Open orders count: {len(orders)}")  # Print the number of open orders
            for order in orders:
                # Print details of each open order
                print(f"Order Ticket: {order.ticket}, Symbol: {order.symbol}, Volume: {order.volume}, Open Price: {order.price_open}, Current Profit: {order.profit}")
            last_notification_time = current_time  # Përditësoni kohën e fundit të njoftimit
            
        for order in orders:
            profit = order.profit
            
            # Kontrollo për fitim
            if profit >= TARGET_PROFIT:
                result = close_order(order)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Failed to close order {order.ticket}, retcode={result.retcode}")
                else:
                    print(f"Order {order.ticket} closed with profit {profit}")
            
            # Kontrollo për humbje
            elif profit <= -TARGET_LOSS:  # Negativ për humbje
                result = close_order(order)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Failed to close order {order.ticket}, retcode={result.retcode}")
                else:
                    print(f"Order {order.ticket} closed with loss {profit}")

    # Përdorni një ndalesë shumë të vogël për të parandaluar ngarkesën e tepërt të CPU-së
    time.sleep(0.1)

# Mbyllja e MT5
mt5.shutdown()
