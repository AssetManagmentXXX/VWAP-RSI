//@version=5
indicator("RSI 40 • Premium Signals (Secuencia + Confirmación)", overlay=true, max_labels_count=500)
 
// ══════════════════════════════════════════════════════════════════
//  GRUPO: CONFIGURACIÓN RSI
// ══════════════════════════════════════════════════════════════════
rsiLength   = input.int   (40,   "Longitud RSI",  minval=1, maxval=200, group="⚙️ RSI")
buyLevel   = input.float (30.0, "Nivel Compra Extremo",  minval=1,  maxval=49, group="⚙️ RSI")
sellLevel  = input.float (70.0, "Nivel Venta Extremo",   minval=51, maxval=99, group="⚙️ RSI")
 
// ══════════════════════════════════════════════════════════════════
//  GRUPO: CONFIGURACIÓN VWAP
// ══════════════════════════════════════════════════════════════════
useVwap     = input.bool  (true, "Activar señales VWAP", group="📈 VWAP")
anchorInput = input.string("Session", "Período de anclaje", options=["Session", "Week", "Month"], group="📈 VWAP")
bandMult    = input.float (1.0, "Multiplicador banda ±1σ", minval=0.1, step=0.1, group="📈 VWAP")
 
// ══════════════════════════════════════════════════════════════════
//  GRUPO: VISUALIZACIÓN Y COLORES
// ══════════════════════════════════════════════════════════════════
showLabels   = input.bool  (true,        "Mostrar etiquetas",   group="🎨 Visual")
showBG       = input.bool  (true,        "Fondo de señal",      group="🎨 Visual")
showArrows   = input.bool  (true,        "Mostrar flechas",     group="🎨 Visual")
showVwapLine = input.bool  (true,        "Mostrar línea VWAP", group="🎨 Visual")
showBands    = input.bool  (true,        "Mostrar bandas ±1σ", group="🎨 Visual")
labelSize    = input.string(size.normal, "Tamaño etiqueta", options=[size.tiny, size.small, size.normal, size.large], group="🎨 Visual")
 
bullColor = input.color(#00C087, "Color Compra Extrema RSI", group="🎨 Visual")
bearColor = input.color(#FF3B5C, "Color Venta Extrema RSI",  group="🎨 Visual")
neutColor = input.color(#F7A600, "Color Neutro",            group="🎨 Visual")
vwapBull  = input.color(#00BFFF, "Color Compra VWAP",        group="🎨 Visual")
vwapBear  = input.color(#FF8C00, "Color Venta VWAP",         group="🎨 Visual")
vwapLine  = input.color(#A0A0FF, "Color línea VWAP",        group="🎨 Visual")
bandColor = input.color(#6A6AFF, "Color bandas ±1σ",        group="🎨 Visual")
 
// ══════════════════════════════════════════════════════════════════
//  CÁLCULOS TÉCNICOS
// ══════════════════════════════════════════════════════════════════
rsi      = ta.rsi(close, rsiLength)
rsiColor = rsi >= sellLevel ? bearColor : rsi <= buyLevel ? bullColor : neutColor
 
anchorTf   = anchorInput == "Week" ? "W" : anchorInput == "Month" ? "M" : "D"
newAnchor  = ta.change(time(anchorTf)) != 0
 
var float sumVol    = 0.0
var float sumTpVol  = 0.0
var float sumTp2Vol = 0.0
 
if newAnchor
    sumVol := 0.0, sumTpVol := 0.0, sumTp2Vol := 0.0
 
sumVol    += volume
sumTpVol  += hlc3 * volume
sumTp2Vol += math.pow(hlc3, 2) * volume
 
vwap       = sumTpVol  / sumVol
vwapVar    = sumTp2Vol / sumVol - math.pow(vwap, 2)
vwapStd    = math.sqrt(math.max(vwapVar, 0))
upperBand1 = vwap + vwapStd * bandMult
lowerBand1 = vwap - vwapStd * bandMult
 
// Dibujar VWAP y bandas
plot(showVwapLine ? vwap       : na, "VWAP",     color=color.new(vwapLine,  20), linewidth=2)
plot(showBands    ? upperBand1 : na, "VWAP +1σ", color=color.new(bandColor, 40), linewidth=1)
plot(showBands    ? lowerBand1 : na, "VWAP -1σ", color=color.new(bandColor, 40), linewidth=1)
 
upperPlot = plot(showBands ? upperBand1 : na, display=display.none)
lowerPlot = plot(showBands ? lowerBand1 : na, display=display.none)
fill(upperPlot, lowerPlot, color=color.new(bandColor, 92))
 
// ══════════════════════════════════════════════════════════════════
//  SEÑALES RSI EXTREMO
// ══════════════════════════════════════════════════════════════════
buySignal  = rsi <= buyLevel  and rsi[1] > buyLevel
sellSignal = rsi >= sellLevel and rsi[1] < sellLevel
 
// ══════════════════════════════════════════════════════════════════
//  MÁQUINA DE ESTADOS SIN FILTRO DE EXTENSIÓN
// ══════════════════════════════════════════════════════════════════
var int vwapState = 0
 
if newAnchor
    vwapState := 0
 
if vwapState == 0
    if high > upperBand1
        vwapState := 1  // Rompe banda superior (Camino a LONG)
    else if low < lowerBand1
        vwapState := 2  // Rompe banda inferior (Camino a SHORT)
 
else if vwapState == 1
    if close < upperBand1
        vwapState := 3  // Reingresa a la banda superior con cierre
 
else if vwapState == 2
    if close > lowerBand1
        vwapState := 4  // Reingresa a la banda inferior con cierre
 
else if vwapState == 3
    if low <= vwap
        vwapState := 5  // Toca el VWAP viniendo de arriba
 
else if vwapState == 4
    if high >= vwap
        vwapState := 6  // Toca el VWAP viniendo de abajo
 
// Filtro de confirmaciones operativas (Toque + Dirección de la vela)
confirmacionBuy  = useVwap and vwapState == 5 and close > open and close > vwap
confirmacionSell = useVwap and vwapState == 6 and close < open and close < vwap
 
vwapTouchBuy  = confirmacionBuy
vwapTouchSell = confirmacionSell
 
// Resetear estado al generar la señal
if vwapTouchBuy or vwapTouchSell
    vwapState := 0
 
// Cancelaciones por invalidez técnica (Precio rompe al extremo opuesto)
if (vwapState == 1 or vwapState == 3 or vwapState == 5) and low < lowerBand1
    vwapState := 2
if (vwapState == 2 or vwapState == 4 or vwapState == 6) and high > upperBand1
    vwapState := 1
 
// ══════════════════════════════════════════════════════════════════
//  ESTADÍSTICAS / VISUALIZACIÓN / ETIQUETAS
// ══════════════════════════════════════════════════════════════════
var int totalBuys      = 0
var int totalSells     = 0
var int totalVwapBuys  = 0
var int totalVwapSells = 0
 
if buySignal
    totalBuys += 1
if sellSignal
    totalSells += 1
if vwapTouchBuy
    totalVwapBuys += 1
if vwapTouchSell
    totalVwapSells += 1
 
bgcolor(showBG and buySignal     ? color.new(bullColor, 85) : na, title="Fondo Compra RSI")
bgcolor(showBG and sellSignal    ? color.new(bearColor, 85) : na, title="Fondo Venta RSI")
bgcolor(showBG and vwapTouchBuy  ? color.new(vwapBull,  88) : na, title="Fondo Compra VWAP")
bgcolor(showBG and vwapTouchSell ? color.new(vwapBear,  88) : na, title="Fondo Venta VWAP")
 
plotshape(showArrows and buySignal,     title = "▲ BUY RSI",          style = shape.triangleup,   location = location.belowbar, color = bullColor, size = size.small)
plotshape(showArrows and sellSignal,    title = "▼ SELL RSI",         style = shape.triangledown, location = location.abovebar, color = bearColor, size = size.small)
plotshape(showArrows and vwapTouchBuy,  title = "◆ BUY TOQUE VWAP",   style = shape.diamond,       location = location.belowbar, color = vwapBull,  size = size.small)
plotshape(showArrows and vwapTouchSell, title = "◆ SELL TOQUE VWAP",  style = shape.diamond,       location = location.abovebar, color = vwapBear,  size = size.small)
 
if showLabels and buySignal
    label.new(bar_index, low, "▲ BUY\nRSI Extremo " + str.tostring(rsi, "#.0"), style=label.style_label_up, color=bullColor, textcolor=color.white, size=labelSize)
if showLabels and sellSignal
    label.new(bar_index, high, "▼ SELL\nRSI Extremo " + str.tostring(rsi, "#.0"), style=label.style_label_down, color=bearColor, textcolor=color.white, size=labelSize)
if showLabels and vwapTouchBuy
    label.new(bar_index, low, "◆ LONG\nRebote VWAP\nRSI " + str.tostring(rsi, "#.0"), style=label.style_label_up, color=vwapBull, textcolor=color.white, size=labelSize)
if showLabels and vwapTouchSell
    label.new(bar_index, high, "◆ SHORT\nRebote VWAP\nRSI " + str.tostring(rsi, "#.0"), style=label.style_label_down, color=vwapBear, textcolor=color.white, size=labelSize)
 
var table panel = table.new(position.top_right, 2, 8, border_color=color.new(color.white, 70), border_width=1, frame_color=color.new(color.white, 60), frame_width=1)
colorHeader = color.new(#1a1a2e, 0)
colorCell   = color.new(#16213e, 0)
 
f_cell(col, row, txt, bg, tc) =>
    table.cell(panel, col, row, txt, bgcolor=bg, text_color=tc, text_size=size.small, text_halign=text.align_center)
 
if barstate.islast
    estado     = rsi >= sellLevel ? "SOBRECOMPRA" : rsi <= buyLevel ? "SOBREVENTA" : "NEUTRAL"
    estadoVwap = vwapState == 1 ? "⏳ Esperando Reingreso a Banda Sup." :
                 vwapState == 3 ? "⏳ Esperando Testeo VWAP (LONG)" :
                 vwapState == 5 ? "⏳ Esperando Vela Verde Confirmación" :
                 vwapState == 2 ? "⏳ Esperando Reingreso a Banda Inf." :
                 vwapState == 4 ? "⏳ Esperando Testeo VWAP (SHORT)" :
                 vwapState == 6 ? "⏳ Esperando Vela Roja Confirmación" : "Buscando Extremos"
 
    f_cell(0, 0, "RSI PREMIUM CONTROL TRADES",    colorHeader, color.white)
    f_cell(1, 0, "📊 " + str.tostring(rsiLength), colorHeader, neutColor)
    f_cell(0, 1, "RSI Actual",                    colorCell,   color.silver)
    f_cell(1, 1, str.tostring(rsi, "#.00"),        colorCell,   rsiColor)
    f_cell(0, 2, "Estado RSI",                    colorCell,   color.silver)
    f_cell(1, 2, estado,                          colorCell,   rsiColor)
    f_cell(0, 3, "Estado VWAP",                   colorCell,   color.silver)
    f_cell(1, 3, estadoVwap,                      colorCell,   color.white)
    f_cell(0, 4, "▲ Compras Extremo RSI",         colorCell,   color.silver)
    f_cell(1, 4, str.tostring(totalBuys),         colorCell,   bullColor)
    f_cell(0, 5, "▼ Ventas Extremo RSI",          colorCell,   color.silver)
    f_cell(1, 5, str.tostring(totalSells),        colorCell,   bearColor)
    f_cell(0, 6, "◆ Longs VWAP",                  colorCell,   color.silver)
    f_cell(1, 6, str.tostring(totalVwapBuys),     colorCell,   vwapBull)
    f_cell(0, 7, "◆ Shorts VWAP",                 colorCell,   color.silver)
    f_cell(1, 7, str.tostring(totalVwapSells),    colorCell,   vwapBear)
