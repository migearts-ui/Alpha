import logging
import os
import re
from decimal import Decimal
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8655920919:AAGIPGfl9EoeImFrTm_kE5HtMxei48BQeJ0")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BCV_URL = "https://www.bcv.org.ve/venezuela/tasas-de-cambio"


async def obtener_tasa_bcv():
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0"}) as client:
            resp = await client.get(BCV_URL)
            texto = resp.text

        match = re.search(r'Dólar[^\d]{0,100}?([\d]{1,3}(?:\.\d{3})*,\d{2})', texto)
        if match:
            valor = match.group(1).replace('.', '').replace(',', '.')
            return Decimal(valor)
    except Exception:
        pass
    return None


async def obtener_precios():
    url = "https://criptoya.com/api/binancep2p/usdt/ves/1"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        data = response.json()
    ask = Decimal(str(data.get("ask", 0)))
    bid = Decimal(str(data.get("bid", 0)))
    return ask, bid


async def usdt_ves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ask, bid = await obtener_precios()
        spread = ask - bid

        mensaje = (
            "💵 Cotización USDT / VES (Bolívares)\n\n"
            f"🔴 Compra: {ask:,.4f} VES   🟢 Venta: {bid:,.4f} VES\n"
            f"📊 Spread: {spread:,.4f} VES\n"
        )

        tasa_bcv = await obtener_tasa_bcv()
        if tasa_bcv and tasa_bcv > 0:
            brecha = ((bid - tasa_bcv) / tasa_bcv) * 100
            mensaje += (
                f"🏦 BCV: {tasa_bcv:,.4f} VES\n"
                f"📈 Brecha: {brecha:,.2f}%\n"
            )

        mensaje += "\nFuente: Binance P2P / BCV"

        await update.message.reply_text(mensaje, parse_mode="Markdown")

    except Exception:
        try:
            url_alt = "https://criptoya.com/api/p2p/usdt/ves"
            async with httpx.AsyncClient(timeout=10) as client:
                resp_alt = await client.get(url_alt)
                data_alt = resp_alt.json()
            promedio = Decimal(str(data_alt.get("binancep2p", {}).get("ask", 0)))

            mensaje = f"💵 Cotización USDT: {promedio:,.4f} VES"

            tasa_bcv = await obtener_tasa_bcv()
            if tasa_bcv and tasa_bcv > 0:
                brecha = ((promedio - tasa_bcv) / tasa_bcv) * 100
                mensaje += (
                    f"\n🏦 BCV: {tasa_bcv:,.4f} VES"
                    f"\n📈 Brecha: {brecha:,.2f}%"
                )

            mensaje += "\nFuente: Binance P2P / BCV"
            await update.message.reply_text(mensaje, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("❌ No se pudo obtener la cotización en este momento.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("usdt", usdt_ves))
    app.add_handler(CommandHandler("precio", usdt_ves))

    print("Bot en marcha (USDT a VES)...")
    app.run_polling()