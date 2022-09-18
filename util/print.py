def print_report(e):
    pnl = e.get_pnl()
    positions = e.get_positions()
    my_trades = e.poll_new_trades(INSTRUMENT_ID)
    all_market_trades = e.poll_new_trade_ticks(INSTRUMENT_ID)
    print(f'I have done {len(my_trades)} trade(s) in {INSTRUMENT_ID} since the last report. There have been {len(all_market_trades)} market trade(s) in total in {INSTRUMENT_ID} since the last report.')
    print(f'My PNL is: {pnl:.2f}')
    print(f'My current positions are: {json.dumps(positions, indent=3)}')


def print_order_response(order_response):
    if order_response.success:
        print(f"Inserted order successfully, order_id='{order_response.order_id}'")
    else:
        print(f"Unable to insert order with reason: '{order_response.success}'")