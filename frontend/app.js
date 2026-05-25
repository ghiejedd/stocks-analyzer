document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('ticker-input');
    const searchBtn = document.getElementById('analyze-btn');
    const dashboard = document.getElementById('dashboard');
    const loader = document.getElementById('loader');
    const errorContainer = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const welcomeHero = document.getElementById('welcome-hero');

    let liveTickerInterval = null;

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    async function performSearch() {
        const ticker = searchInput.value.trim();
        if (!ticker) return;

        // Reset UI & Stop previous ticker & Hide welcome landing
        if (liveTickerInterval) clearInterval(liveTickerInterval);
        welcomeHero.style.display = 'none';
        
        dashboard.classList.remove('active');
        setTimeout(() => {
            dashboard.style.display = 'none';
            errorContainer.style.display = 'none';
            loader.style.display = 'block';
        }, 150);

        try {
            const response = await fetch(`/api/analyze/${ticker}`);
            
            if (!response.ok) {
                let errorMsg = 'Terjadi kesalahan saat mengambil data';
                try {
                    const rawText = await response.text();
                    try {
                        const errData = JSON.parse(rawText);
                        errorMsg = errData.detail || errorMsg;
                    } catch (jsonErr) {
                        if (rawText && rawText.length < 200) {
                            errorMsg = rawText;
                        }
                    }
                } catch (textErr) {}
                throw new Error(errorMsg);
            }

            const data = await response.json();

            // Small delay to make shimmer skeleton feel premium
            setTimeout(() => {
                try {
                    renderDashboard(data);
                    loader.style.display = 'none';
                    dashboard.style.display = 'block';
                    
                    // Trigger smooth fade-in
                    setTimeout(() => {
                        dashboard.classList.add('active');
                    }, 50);
                } catch (renderErr) {
                    console.error("Gagal me-render dashboard:", renderErr);
                    loader.style.display = 'none';
                    errorText.textContent = `Gagal me-render dashboard: ${renderErr.message}`;
                    errorContainer.style.display = 'flex';
                }
            }, 800);

        } catch (err) {
            loader.style.display = 'none';
            errorText.textContent = err.message;
            errorContainer.style.display = 'flex';
        }
    }

    // Expose quick search globally for welcome screen popular stocks suggestion buttons
    window.quickSearch = (ticker) => {
        searchInput.value = ticker;
        performSearch();
    };

    // Welcome Screen Carousel Slideshow Logic
    let currentSlide = 0;
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.dot');
    let slideInterval = null;

    function showSlide(index) {
        if (slides.length === 0) return;
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        
        currentSlide = (index + slides.length) % slides.length;
        slides[currentSlide].classList.add('active');
        if (dots[currentSlide]) dots[currentSlide].classList.add('active');
    }

    window.setSlide = (index) => {
        showSlide(index);
        resetSlideTimer();
    };

    function startSlideTimer() {
        if (slides.length === 0) return;
        slideInterval = setInterval(() => {
            showSlide(currentSlide + 1);
        }, 4500);
    }

    function resetSlideTimer() {
        if (slideInterval) {
            clearInterval(slideInterval);
            startSlideTimer();
        }
    }

    // Initialize slide timer
    startSlideTimer();

    // PCA-EVA Detail Toggle Button
    const togglePcaBtn = document.getElementById('toggle-pca-btn');
    const pcaTableBox = document.getElementById('pca-indicators-table-box');
    if (togglePcaBtn && pcaTableBox) {
        togglePcaBtn.addEventListener('click', () => {
            if (pcaTableBox.style.display === 'none') {
                pcaTableBox.style.display = 'block';
                togglePcaBtn.textContent = 'Sembunyikan Detail 11 Indikator PCA-EVA ▲';
            } else {
                pcaTableBox.style.display = 'none';
                togglePcaBtn.textContent = 'Tampilkan Detail 11 Indikator PCA-EVA ▼';
            }
        });
    }

    function renderDashboard(data) {
        // --- 1. Company Profile Header & Logo ---
        const profile = data.profile;
        const cleanTicker = data.ticker.replace('.JK', '').replace('.jk', '').toUpperCase();
        const companyName = profile.name || cleanTicker;
        
        // TradingView-like perfect logo & avatar handler
        setDynamicLogo(companyName, cleanTicker, profile.logo, profile.logo_hd, profile.domain);
        
        document.getElementById('stock-ticker').textContent = cleanTicker;
        document.getElementById('stock-sector').textContent = profile.sector;
        document.getElementById('company-name').textContent = companyName;
        document.getElementById('company-industry').textContent = profile.industry;
        
        const webLink = document.getElementById('company-website');
        if (profile.website && profile.website !== 'N/A') {
            webLink.href = profile.website;
            webLink.style.display = 'inline-flex';
        } else {
            webLink.style.display = 'none';
        }

        // --- 2. Price & Change Percentage ---
        const price = data.fundamental.market_info.price;
        const change = data.teknikal.change_pct;
        
        document.getElementById('stock-price').textContent = price ? `Rp ${price.toLocaleString('id-ID')}` : 'N/A';
        
        const changeEl = document.getElementById('stock-change');
        if (change !== null) {
            changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.className = `price-change ${change >= 0 ? 'text-green' : 'text-red'}`;
        } else {
            changeEl.textContent = '0.00%';
            changeEl.className = 'price-change';
        }

        // Composite Target Price Rendering
        const targetPrice = data.target_price;
        const targetEl = document.getElementById('stock-target-price');
        if (targetPrice && targetPrice > 0) {
            targetEl.textContent = `Target: Rp ${targetPrice.toLocaleString('id-ID')}`;
            targetEl.style.display = 'inline-flex';
            
            const cmpPrice = price || 0;
            if (cmpPrice > 0 && targetPrice > cmpPrice) {
                targetEl.style.color = 'var(--accent-green)';
                targetEl.style.background = 'rgba(16, 185, 129, 0.08)';
                targetEl.style.border = '1px solid rgba(16, 185, 129, 0.25)';
            } else if (cmpPrice > 0 && targetPrice < cmpPrice) {
                targetEl.style.color = 'var(--accent-red)';
                targetEl.style.background = 'rgba(244, 63, 94, 0.08)';
                targetEl.style.border = '1px solid rgba(244, 63, 94, 0.25)';
            } else {
                targetEl.style.color = 'var(--accent-yellow)';
                targetEl.style.background = 'rgba(245, 158, 11, 0.08)';
                targetEl.style.border = '1px solid rgba(245, 158, 11, 0.25)';
            }
        } else {
            targetEl.style.display = 'none';
        }

        // --- 3. Dynamic Radial Gauge & Recommendation ---
        const totalSkor = data.total_skor;
        const gaugeScore = document.getElementById('gauge-score');
        gaugeScore.textContent = totalSkor > 0 ? `+${totalSkor}` : totalSkor;
        
        const circleProgress = Math.min(Math.max(((totalSkor + 12) / 24) * 100, 10), 100);
        const progressPath = document.getElementById('gauge-progress');
        progressPath.setAttribute('stroke-dasharray', `${circleProgress}, 100`);

        const rekomEl = document.getElementById('main-rekomendasi');
        rekomEl.textContent = data.rekomendasi;
        
        let accentColor = 'var(--accent-yellow)';
        let cardClass = '';
        if (data.rekomendasi.includes('BUY')) {
            accentColor = 'var(--accent-green)';
            progressPath.setAttribute('stroke', 'var(--accent-green)');
            rekomEl.style.color = 'var(--accent-green)';
            rekomEl.style.border = '1px solid rgba(16, 185, 129, 0.4)';
            rekomEl.style.background = 'rgba(16, 185, 129, 0.08)';
            cardClass = 'card-bullish';
        } else if (data.rekomendasi.includes('SELL')) {
            accentColor = 'var(--accent-red)';
            progressPath.setAttribute('stroke', 'var(--accent-red)');
            rekomEl.style.color = 'var(--accent-red)';
            rekomEl.style.border = '1px solid rgba(244, 63, 94, 0.4)';
            rekomEl.style.background = 'rgba(244, 63, 94, 0.08)';
            cardClass = 'card-bearish';
        } else {
            accentColor = 'var(--accent-yellow)';
            progressPath.setAttribute('stroke', 'var(--accent-yellow)');
            rekomEl.style.color = 'var(--accent-yellow)';
            rekomEl.style.border = '1px solid rgba(245, 158, 11, 0.4)';
            rekomEl.style.background = 'rgba(245, 158, 11, 0.08)';
        }

        document.querySelectorAll('.card').forEach(card => {
            card.className = 'card glass';
            if (cardClass) card.classList.add(cardClass);
        });

        // --- 4. Render Components ---
        renderFundamental(data.fundamental);
        renderTeknikal(data.teknikal);
        renderBroker(data.broker);
        renderIntraday(data.intraday);
        renderFibonacci(data.teknikal.fibonacci, price);
        renderOrderBook(data.orderbook);
        renderSupportResistance(data.support_resistance);
        renderTradingViewChart(data.ticker);
        renderNews(data.news);
        renderPCA(data.pca_eva);
        renderStatisticalArbitrage(data.statistical_arbitrage, data.ticker);
        renderCrashMomentum(data.crash_momentum);
        renderHybridForecast(data.hybrid_forecast);
        renderUMAShield(data.uma_filter);
        renderMeanReversionOU(data.mean_reversion_ou);
        renderCompanyProfile(profile.summary);
        // --- 5. Clean up previous price pooling & start new polling ---
        if (liveTickerInterval) {
            clearInterval(liveTickerInterval);
        }
        startPricePooling(data.ticker);
    }

    // TradingView-like perfect logo & fallback avatar sequence (HD 256px)
    function setDynamicLogo(companyName, cleanTicker, logoUrl, logoHdUrl, domain) {
        const wrapper = document.querySelector('.logo-wrapper');
        wrapper.innerHTML = ''; // Reset container
        
        const logoFallbacks = [];
        
        // Priority 1: Stockbit's official high-res PNG company logos CDN for Indonesian Emitens
        if (cleanTicker) {
            logoFallbacks.push(`https://assets.stockbit.com/logos/companies/${cleanTicker.toUpperCase()}.png`);
        }
        
        if (logoHdUrl) logoFallbacks.push(logoHdUrl);
        if (logoUrl) logoFallbacks.push(logoUrl);
        if (domain) {
            logoFallbacks.push(`https://img.logo.dev/${domain}?token=pk_anonymous&size=256&format=png`);
            logoFallbacks.push(`https://www.google.com/s2/favicons?domain=www.${domain}&sz=256`);
            logoFallbacks.push(`https://logo.clearbit.com/${domain}?size=256`);
        }
        
        if (logoFallbacks.length > 0) {
            const img = document.createElement('img');
            img.id = 'company-logo';
            img.className = 'company-logo';
            img.alt = companyName;
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease';
            img.style.objectFit = 'contain';
            
            let currentIdx = 0;
            img.src = logoFallbacks[currentIdx];
            
            img.onload = () => {
                // Skip tiny placeholder favicons (typically 16x16)
                if (img.naturalWidth <= 20 && currentIdx < logoFallbacks.length - 1) {
                    currentIdx++;
                    img.src = logoFallbacks[currentIdx];
                    return;
                }
                img.style.opacity = '1';
                wrapper.style.background = 'transparent'; // Keep background transparent for a premium look
            };
            
            img.onerror = () => {
                currentIdx++;
                if (currentIdx < logoFallbacks.length) {
                    img.src = logoFallbacks[currentIdx];
                } else {
                    renderTextAvatar(wrapper, cleanTicker);
                }
            };
            
            wrapper.appendChild(img);
        } else {
            renderTextAvatar(wrapper, cleanTicker);
        }
    }

    function renderTextAvatar(container, ticker) {
        const initials = ticker.substring(0, 2).toUpperCase();
        
        // Generate stunning gradient colors based on ticker letters
        const gradientList = [
            ['#00df89', '#031413'], // GE Vernova electric green to deep forest
            ['#09ECA9', '#052221'], // Glowing mint to dark slate green
            ['#10b981', '#031413'], // Emerald to deep forest
            ['#34d399', '#052221'], // Mint green to dark slate
            ['#059669', '#022c22'], // Classic deep emerald
            ['#00f097', '#064e3b']  // Electric bright green to dark forest
        ];
        
        const charSum = ticker.charCodeAt(0) + (ticker.charCodeAt(1) || 0);
        const grad = gradientList[charSum % gradientList.length];
        
        container.style.background = 'none'; // Clear default wrapper bg
        container.innerHTML = `
            <div class="text-avatar" style="
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, ${grad[0]}, ${grad[1]});
                color: #ffffff;
                font-family: 'Outfit', sans-serif;
                font-size: 24px;
                font-weight: 800;
                letter-spacing: -0.5px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.25);
                animation: fadeIn 0.4s ease;
            ">${initials}</div>
        `;
    }
    function renderFundamental(data) {
        const skorEl = document.getElementById('fund-skor');
        skorEl.textContent = data.skor > 0 ? `+${data.skor}` : data.skor;
        skorEl.className = `score ${data.skor >= 0 ? 'text-green' : 'text-red'}`;

        const alasanList = document.getElementById('fund-alasan');
        alasanList.innerHTML = data.alasan.map(a => `<li>${a}</li>`).join('');

        // Valuasi
        const valuasiGrid = document.getElementById('fund-valuasi');
        valuasiGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">PER (TTM)</span><span class="metric-value">${data.valuasi.per}</span></div>
            <div class="metric-item"><span class="metric-label">Forward PE</span><span class="metric-value">${data.valuasi.fwd_pe}</span></div>
            <div class="metric-item"><span class="metric-label">PEG Ratio</span><span class="metric-value">${data.valuasi.peg}</span></div>
            <div class="metric-item"><span class="metric-label">PBV</span><span class="metric-value">${data.valuasi.pbv}</span></div>
            <div class="metric-item"><span class="metric-label">P/S (TTM)</span><span class="metric-value">${data.valuasi.ps}</span></div>
            <div class="metric-item"><span class="metric-label">EV/EBITDA</span><span class="metric-value">${data.valuasi.ev_ebitda}</span></div>
            <div class="metric-item"><span class="metric-label">EV/Revenue</span><span class="metric-value">${data.valuasi.ev_rev}</span></div>
        `;

        // Profitabilitas
        const profitGrid = document.getElementById('fund-profitabilitas');
        profitGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">ROE</span><span class="metric-value">${data.profitabilitas.roe}</span></div>
            <div class="metric-item"><span class="metric-label">ROA</span><span class="metric-value">${data.profitabilitas.roa}</span></div>
            <div class="metric-item"><span class="metric-label">Gross Margin</span><span class="metric-value">${data.profitabilitas.gpm}</span></div>
            <div class="metric-item"><span class="metric-label">EBITDA Margin</span><span class="metric-value">${data.profitabilitas.ebitda_margin}</span></div>
            <div class="metric-item"><span class="metric-label">Operating Margin</span><span class="metric-value">${data.profitabilitas.opm}</span></div>
            <div class="metric-item"><span class="metric-label">Net Profit Margin</span><span class="metric-value">${data.profitabilitas.npm}</span></div>
        `;

        // Laporan Keuangan
        const lkGrid = document.getElementById('fund-lk');
        lkGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Revenue</span><span class="metric-value">${data.laporan_keuangan.rev}</span></div>
            <div class="metric-item"><span class="metric-label">EBITDA</span><span class="metric-value">${data.laporan_keuangan.ebitda}</span></div>
            <div class="metric-item"><span class="metric-label">Net Income</span><span class="metric-value">${data.laporan_keuangan.ni}</span></div>
            <div class="metric-item"><span class="metric-label">EPS (TTM)</span><span class="metric-value">${data.laporan_keuangan.eps}</span></div>
            <div class="metric-item"><span class="metric-label">Forward EPS</span><span class="metric-value">${data.laporan_keuangan.fwd_eps}</span></div>
            <div class="metric-item"><span class="metric-label">Book Value/Share</span><span class="metric-value">${data.laporan_keuangan.bv}</span></div>
            <div class="metric-item"><span class="metric-label">Total Debt</span><span class="metric-value">${data.laporan_keuangan.td}</span></div>
            <div class="metric-item"><span class="metric-label">Total Cash</span><span class="metric-value">${data.laporan_keuangan.tc}</span></div>
            <div class="metric-item"><span class="metric-label">Operating CF</span><span class="metric-value">${data.laporan_keuangan.ocf}</span></div>
            <div class="metric-item"><span class="metric-label">Free Cash Flow</span><span class="metric-value">${data.laporan_keuangan.fcf}</span></div>
            <div class="metric-item"><span class="metric-label">DER</span><span class="metric-value">${data.laporan_keuangan.der}</span></div>
            <div class="metric-item"><span class="metric-label">Current Ratio</span><span class="metric-value">${data.laporan_keuangan.cr}</span></div>
            <div class="metric-item"><span class="metric-label">Quick Ratio</span><span class="metric-value">${data.laporan_keuangan.qr}</span></div>
        `;

        // Pertumbuhan
        const growthGrid = document.getElementById('fund-pertumbuhan');
        growthGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Revenue Growth (YoY)</span><span class="metric-value">${data.pertumbuhan.rev_growth_yoy}</span></div>
            <div class="metric-item"><span class="metric-label">Earnings Growth (YoY)</span><span class="metric-value">${data.pertumbuhan.earn_growth_yoy}</span></div>
            <div class="metric-item"><span class="metric-label">Revenue Growth (QoQ)</span><span class="metric-value">${data.pertumbuhan.rev_growth_qoq}</span></div>
            <div class="metric-item"><span class="metric-label">Earnings Growth (QoQ)</span><span class="metric-value">${data.pertumbuhan.earn_growth_qoq}</span></div>
        `;

        // Market Info
        const marketGrid = document.getElementById('fund-market');
        marketGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Market Cap</span><span class="metric-value">${data.market_info.mcap}</span></div>
            <div class="metric-item"><span class="metric-label">Enterprise Value</span><span class="metric-value">${data.market_info.ev}</span></div>
            <div class="metric-item"><span class="metric-label">Beta</span><span class="metric-value">${data.market_info.beta}</span></div>
            <div class="metric-item"><span class="metric-label">Avg Volume</span><span class="metric-value">${data.market_info.avg_vol}</span></div>
            <div class="metric-item"><span class="metric-label">52W High</span><span class="metric-value">${data.market_info.hi52}</span></div>
            <div class="metric-item"><span class="metric-label">52W Low</span><span class="metric-value">${data.market_info.lo52}</span></div>
            <div class="metric-item"><span class="metric-label">% dari 52W High</span><span class="metric-value ${data.market_info.pct_from_hi && data.market_info.pct_from_hi.startsWith('-') ? 'text-red' : 'text-green'}">${data.market_info.pct_from_hi}</span></div>
            <div class="metric-item"><span class="metric-label">% dari 52W Low</span><span class="metric-value ${data.market_info.pct_from_lo && data.market_info.pct_from_lo.startsWith('+') ? 'text-green' : 'text-red'}">${data.market_info.pct_from_lo}</span></div>
            <div class="metric-item"><span class="metric-label">Dividend Yield</span><span class="metric-value">${data.market_info.dy}</span></div>
            <div class="metric-item"><span class="metric-label">Dividend/Share</span><span class="metric-value">${data.market_info.dps}</span></div>
            <div class="metric-item"><span class="metric-label">Payout Ratio</span><span class="metric-value">${data.market_info.payout}</span></div>
        `;

        // DCF Valuation Box
        const dcfVal = data.valuasi.dcf_val;
        const dcfDiff = data.valuasi.dcf_diff;
        const dcfStatus = data.valuasi.dcf_status;
        const dcfParams = data.valuasi.dcf_params;

        document.getElementById('dcf-val').textContent = dcfVal;
        
        const dcfDiffEl = document.getElementById('dcf-diff');
        dcfDiffEl.textContent = dcfDiff;
        if (dcfDiff && dcfDiff.startsWith('+')) {
            dcfDiffEl.className = 'text-green';
        } else if (dcfDiff && dcfDiff.startsWith('-')) {
            dcfDiffEl.className = 'text-red';
        } else {
            dcfDiffEl.className = '';
        }

        const dcfStatusEl = document.getElementById('dcf-status');
        dcfStatusEl.textContent = dcfStatus;
        if (dcfStatus && dcfStatus.includes('UNDERVALUED')) {
            dcfStatusEl.style.color = 'var(--accent-green)';
        } else if (dcfStatus && dcfStatus.includes('OVERVALUED')) {
            dcfStatusEl.style.color = 'var(--accent-red)';
        } else {
            dcfStatusEl.style.color = 'var(--text-secondary)';
        }
        document.getElementById('dcf-params').textContent = dcfParams;

        // Graham Valuation Box
        const gVal = data.valuasi.graham_val;
        const gDiff = data.valuasi.graham_diff;
        const gStatus = data.valuasi.graham_status;

        document.getElementById('graham-val').textContent = gVal;
        
        const gDiffEl = document.getElementById('graham-diff');
        gDiffEl.textContent = gDiff;
        if (gDiff && gDiff.startsWith('+')) {
            gDiffEl.className = 'text-green';
        } else if (gDiff && gDiff.startsWith('-')) {
            gDiffEl.className = 'text-red';
        } else {
            gDiffEl.className = '';
        }
        
        const gStatusEl = document.getElementById('graham-status');
        gStatusEl.textContent = gStatus;
        if (gStatus && gStatus.includes('UNDERVALUED')) {
            gStatusEl.style.color = 'var(--accent-green)';
        } else if (gStatus && gStatus.includes('OVERVALUED')) {
            gStatusEl.style.color = 'var(--accent-red)';
        } else {
            gStatusEl.style.color = 'var(--text-secondary)';
        }

        // Piotroski F-Score & Altman Z-Score Box
        document.getElementById('piotroski-val').textContent = data.valuasi.piotroski_val;
        document.getElementById('altman-val').textContent = data.valuasi.altman_val;
        
        const altmanStatusEl = document.getElementById('altman-status');
        altmanStatusEl.textContent = data.valuasi.altman_status;
        if (data.valuasi.altman_status && data.valuasi.altman_status.includes('Safe')) {
            altmanStatusEl.style.color = 'var(--accent-green)';
        } else if (data.valuasi.altman_status && data.valuasi.altman_status.includes('Distress')) {
            altmanStatusEl.style.color = 'var(--accent-red)';
        } else {
            altmanStatusEl.style.color = 'var(--accent-yellow)';
        }
    }

    function renderTeknikal(data) {
        const skorEl = document.getElementById('tek-skor');
        skorEl.textContent = data.skor > 0 ? `+${data.skor}` : data.skor;
        skorEl.className = `score ${data.skor >= 0 ? 'text-green' : 'text-red'}`;

        // Trend Summary Badge
        const trendBadge = document.getElementById('trend-summary-badge');
        if (data.trend_summary) {
            trendBadge.textContent = `${data.trend_summary.label} (Score: ${data.trend_summary.score})`;
            if (data.trend_summary.label.includes('UPTREND')) {
                trendBadge.style.color = 'var(--accent-green)';
                trendBadge.style.background = 'rgba(16, 185, 129, 0.08)';
                trendBadge.style.borderColor = 'rgba(16, 185, 129, 0.2)';
            } else if (data.trend_summary.label.includes('DOWNTREND')) {
                trendBadge.style.color = 'var(--accent-red)';
                trendBadge.style.background = 'rgba(244, 63, 94, 0.08)';
                trendBadge.style.borderColor = 'rgba(244, 63, 94, 0.2)';
            } else {
                trendBadge.style.color = 'var(--accent-yellow)';
                trendBadge.style.background = 'rgba(245, 158, 11, 0.08)';
                trendBadge.style.borderColor = 'rgba(245, 158, 11, 0.2)';
            }
        }

        // Zero-Trade Shield
        const ztBox = document.getElementById('zero-trade-shield-box');
        const ztStatus = document.getElementById('zt-shield-status');
        const ztDetails = document.getElementById('zt-shield-details');
        
        if (ztBox && data.zero_trade_prevention) {
            ztBox.style.display = 'block';
            const zt = data.zero_trade_prevention;
            if (zt.triggered) {
                ztStatus.textContent = 'TERPICU (SINYAL BELI / BUY TRIGGERED)';
                ztStatus.className = 'text-green font-bold';
                ztDetails.textContent = `Tren Bullish Kuat (ADX: ${zt.adx.toFixed(1)} > 20, Close > EMA50) + RSI Pullback Recovery (${zt.rsi.toFixed(1)} memotong ke atas 40). Eksekusi Beli Taktis Aktif!`;
                ztBox.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                ztBox.style.background = 'rgba(16, 185, 129, 0.08)';
            } else {
                ztStatus.textContent = 'AKTIF / MENGAMATI (STANDBY)';
                ztStatus.className = 'text-yellow';
                let detailsStr = `Sistem memisahkan kekuatan tren (ADX: ${zt.adx.toFixed(1)} ${zt.adx > 20 ? '> 20 ✓' : '≤ 20'}) `;
                detailsStr += `dan posisi harga vs EMA50 (${zt.ema50 ? 'Close ' + (zt.trend_bullish ? '>' : '<=') + ' EMA50' : 'N/A'}). `;
                detailsStr += `Status RSI saat ini: ${zt.rsi.toFixed(1)}. Menunggu kondisi RSI Pullback Recovery (RSI < 40 lalu crossing di atas 40) untuk memicu entri belanja.`;
                ztDetails.textContent = detailsStr;
                ztBox.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                ztBox.style.background = 'rgba(0, 0, 0, 0.2)';
            }
        } else if (ztBox) {
            ztBox.style.display = 'none';
        }

        const alasanList = document.getElementById('tek-alasan');
        alasanList.innerHTML = data.alasan.map(a => `<li>${a}</li>`).join('');

        // 1. Tren & Rerata Bergerak
        const maGrid = document.getElementById('tek-ma');
        const cro = data.ma.crossover || 'TIDAK ADA CROSSOVER';
        let croClass = 'text-muted';
        if (cro.includes('GOLDEN')) croClass = 'text-green font-bold';
        else if (cro.includes('DEATH')) croClass = 'text-red font-bold';

        maGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">MA 7 (Short-term)</span><span class="metric-value">${data.ma.ma7 ? 'Rp ' + Math.round(data.ma.ma7).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MA 20 (Medium-term)</span><span class="metric-value">${data.ma.ma20 ? 'Rp ' + Math.round(data.ma.ma20).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MA 50 (Semi Long-term)</span><span class="metric-value">${data.ma.ma50 ? 'Rp ' + Math.round(data.ma.ma50).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">EMA 200 (Long-term)</span><span class="metric-value">${data.ema200 ? 'Rp ' + Math.round(data.ema200).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MA Crossover</span><span class="metric-value ${croClass}">${cro}</span></div>
        `;

        // 2. Osilator & Momentum
        const oscGrid = document.getElementById('tek-oscillator');
        
        // RSI color coding
        let rsiClass = '';
        if (data.rsi < 30) rsiClass = 'text-green';
        else if (data.rsi > 70) rsiClass = 'text-red';
        
        // StochRSI color coding
        let stochClass = '';
        if (data.stoch_rsi < 20) stochClass = 'text-green';
        else if (data.stoch_rsi > 80) stochClass = 'text-red';
        
        // Williams %R color coding
        let wrClass = '';
        if (data.williams_r < -80) wrClass = 'text-green';
        else if (data.williams_r > -20) wrClass = 'text-red';

        // MACD crossover coloring
        const macdCro = data.macd.crossover || 'NETRAL';
        let mCroClass = 'text-muted';
        if (macdCro.includes('BULLISH')) mCroClass = 'text-green';
        else if (macdCro.includes('BEARISH')) mCroClass = 'text-red';

        // ADX color coding
        let adxTrend = 'Netral';
        let adxClass = 'text-muted';
        if (data.adx.adx > 25) {
            if (data.adx.pdi > data.adx.mdi) {
                adxTrend = 'Tren Naik Kuat';
                adxClass = 'text-green';
            } else {
                adxTrend = 'Tren Turun Kuat';
                adxClass = 'text-red';
            }
        }

        oscGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">RSI (14)</span><span class="metric-value ${rsiClass}">${data.rsi ? data.rsi.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">StochRSI (14)</span><span class="metric-value ${stochClass}">${data.stoch_rsi ? data.stoch_rsi.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Williams %R</span><span class="metric-value ${wrClass}">${data.williams_r ? data.williams_r.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">ADX (Kekuatan Tren)</span><span class="metric-value ${adxClass}">${data.adx.adx ? data.adx.adx.toFixed(2) : 'N/A'} (${adxTrend})</span></div>
            <div class="metric-item"><span class="metric-label">Plus DI (+DI)</span><span class="metric-value text-green">${data.adx.pdi ? data.adx.pdi.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Minus DI (-DI)</span><span class="metric-value text-red">${data.adx.mdi ? data.adx.mdi.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MACD Value</span><span class="metric-value">${data.macd.macd ? data.macd.macd.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MACD Signal</span><span class="metric-value">${data.macd.signal ? data.macd.signal.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MACD Hist</span><span class="metric-value ${data.macd.hist > 0 ? 'text-green' : data.macd.hist < 0 ? 'text-red' : ''}">${data.macd.hist ? data.macd.hist.toFixed(2) : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">MACD Crossover</span><span class="metric-value ${mCroClass}">${macdCro}</span></div>
        `;

        // 3. Volatilitas & Jangkauan
        const volGrid = document.getElementById('tek-volatility');
        volGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Bollinger Upper BB</span><span class="metric-value">${data.bb.upper ? 'Rp ' + Math.round(data.bb.upper).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Bollinger Mid BB</span><span class="metric-value">${data.bb.mid ? 'Rp ' + Math.round(data.bb.mid).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Bollinger Lower BB</span><span class="metric-value">${data.bb.lower ? 'Rp ' + Math.round(data.bb.lower).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">BB Width (Volatilitas)</span><span class="metric-value">${data.bb.width ? data.bb.width.toFixed(2) + '%' : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">ATR (14) (Range Harian)</span><span class="metric-value">${data.atr ? 'Rp ' + Math.round(data.atr).toLocaleString('id-ID') : 'N/A'}</span></div>
        `;

        // 4. Indikator Lanjutan
        const advGrid = document.getElementById('tek-advanced');
        const ichSig = data.ichimoku ? data.ichimoku.signal : 'N/A';
        const ichClass = ichSig.includes('BULLISH') ? 'text-green' : ichSig.includes('BEARISH') ? 'text-red' : 'text-yellow';
        
        const psarTrend = data.parabolic_sar ? data.parabolic_sar.trend : 'N/A';
        const psarClass = psarTrend === 'UPTREND' ? 'text-green' : psarTrend === 'DOWNTREND' ? 'text-red' : '';

        advGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Ichimoku Signal</span><span class="metric-value ${ichClass}">${ichSig}</span></div>
            <div class="metric-item"><span class="metric-label">Tenkan-sen</span><span class="metric-value">${data.ichimoku.tenkan ? 'Rp ' + Math.round(data.ichimoku.tenkan).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Kijun-sen</span><span class="metric-value">${data.ichimoku.kijun ? 'Rp ' + Math.round(data.ichimoku.kijun).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Senkou Span A</span><span class="metric-value">${data.ichimoku.senkou_a ? 'Rp ' + Math.round(data.ichimoku.senkou_a).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Senkou Span B</span><span class="metric-value">${data.ichimoku.senkou_b ? 'Rp ' + Math.round(data.ichimoku.senkou_b).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Parabolic SAR</span><span class="metric-value ${psarClass}">${data.parabolic_sar.value ? 'Rp ' + Math.round(data.parabolic_sar.value).toLocaleString('id-ID') : 'N/A'} (${psarTrend})</span></div>
            <div class="metric-item"><span class="metric-label">VWAP Value</span><span class="metric-value">${data.vwap.vwap ? 'Rp ' + Math.round(data.vwap.vwap).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">VWAP Upper Band</span><span class="metric-value">${data.vwap.upper ? 'Rp ' + Math.round(data.vwap.upper).toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">VWAP Lower Band</span><span class="metric-value">${data.vwap.lower ? 'Rp ' + Math.round(data.vwap.lower).toLocaleString('id-ID') : 'N/A'}</span></div>
        `;

        // 5. Candlestick & Volume
        const candVolGrid = document.getElementById('tek-candlestick-vol');
        const patternStr = data.patterns && data.patterns.length > 0 ? data.patterns.join(', ') : 'Tidak Ada Pola Terdeteksi';
        const isBullishPattern = data.patterns && data.patterns.some(p => p.includes('BULLISH') || p.includes('HAMMER') || p.includes('MORNING'));
        const isBearishPattern = data.patterns && data.patterns.some(p => p.includes('BEARISH') || p.includes('SHOOTING') || p.includes('EVENING'));
        let patternClass = 'text-muted';
        if (isBullishPattern) patternClass = 'text-green font-bold';
        else if (isBearishPattern) patternClass = 'text-red font-bold';

        candVolGrid.innerHTML = `
            <div class="metric-item"><span class="metric-label">Pola Candlestick</span><span class="metric-value ${patternClass}">${patternStr}</span></div>
            <div class="metric-item"><span class="metric-label">Volume Transaksi</span><span class="metric-value">${data.volume.vol ? data.volume.vol.toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Rata-rata Volume (20D)</span><span class="metric-value">${data.volume.vol_ma20 ? data.volume.vol_ma20.toLocaleString('id-ID') : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Rasio Volume vs MA20</span><span class="metric-value">${(data.volume.vol && data.volume.vol_ma20) ? (data.volume.vol / data.volume.vol_ma20).toFixed(2) + 'x' : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Buy Pressure (Orderbook)</span><span class="metric-value text-green">${data.orderbook.buy_pressure ? data.orderbook.buy_pressure.toFixed(1) + '%' : 'N/A'}</span></div>
            <div class="metric-item"><span class="metric-label">Sell Pressure (Orderbook)</span><span class="metric-value text-red">${data.orderbook.sell_pressure ? data.orderbook.sell_pressure.toFixed(1) + '%' : 'N/A'}</span></div>
        `;
    }

    function renderBroker(data) {
        const skorEl = document.getElementById('broker-skor');
        skorEl.textContent = data.skor > 0 ? `+${data.skor}` : data.skor;
        skorEl.className = `score ${data.skor >= 0 ? 'text-green' : 'text-red'}`;

        const faseBadge = document.getElementById('broker-fase');
        faseBadge.textContent = data.fase;
        if (data.fase.includes('AKUMULASI')) {
            faseBadge.style.color = 'var(--accent-green)';
            faseBadge.style.background = 'rgba(16, 185, 129, 0.08)';
            faseBadge.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        } else if (data.fase.includes('DISTRIBUSI')) {
            faseBadge.style.color = 'var(--accent-red)';
            faseBadge.style.background = 'rgba(244, 63, 94, 0.08)';
            faseBadge.style.borderColor = 'rgba(244, 63, 94, 0.2)';
        } else {
            faseBadge.style.color = 'var(--text-secondary)';
            faseBadge.style.background = 'rgba(255, 255, 255, 0.04)';
            faseBadge.style.borderColor = 'rgba(255, 255, 255, 0.06)';
        }

        const alasanList = document.getElementById('broker-alasan');
        alasanList.innerHTML = data.alasan.map(a => `<li>${a}</li>`).join('');

        const metricsGrid = document.getElementById('broker-metrics');
        metricsGrid.innerHTML = `
            <div class="metric-item">
                <span class="metric-label">MFI (Flow)</span>
                <span class="metric-value">${data.smart_money.mfi ? data.smart_money.mfi.toFixed(1) : 'N/A'}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">CMF</span>
                <span class="metric-value ${data.smart_money.cmf > 0 ? 'text-green' : data.smart_money.cmf < 0 ? 'text-red' : ''}">${data.smart_money.cmf ? data.smart_money.cmf.toFixed(4) : 'N/A'}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Vol Ratio</span>
                <span class="metric-value">${data.smart_money.vol_ratio ? data.smart_money.vol_ratio.toFixed(2) + 'x' : 'N/A'}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Buy/Sell 5D</span>
                <span class="metric-value ${data.buy_pct > 55 ? 'text-green' : data.sell_pct > 55 ? 'text-red' : ''}">${data.buy_pct.toFixed(0)}% / ${data.sell_pct.toFixed(0)}%</span>
            </div>
        `;
    }

    function renderIntraday(data) {
        const skorEl = document.getElementById('intra-skor');
        skorEl.textContent = data.skor > 0 ? `+${data.skor}` : data.skor;
        skorEl.className = `score ${data.skor >= 0 ? 'text-green' : 'text-red'}`;

        const kesimpulan = document.getElementById('intra-kesimpulan');
        kesimpulan.textContent = data.kesimpulan;
        if (data.kesimpulan.includes('BELI PAGI')) {
            kesimpulan.style.color = 'var(--accent-green)';
            kesimpulan.style.background = 'rgba(16, 185, 129, 0.08)';
            kesimpulan.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        } else if (data.kesimpulan.includes('BELI SORE')) {
            kesimpulan.style.color = 'var(--accent-blue)';
            kesimpulan.style.background = 'rgba(59, 130, 246, 0.08)';
            kesimpulan.style.borderColor = 'rgba(59, 130, 246, 0.2)';
        } else {
            kesimpulan.style.color = 'var(--text-secondary)';
            kesimpulan.style.background = 'rgba(255, 255, 255, 0.04)';
            kesimpulan.style.borderColor = 'rgba(255, 255, 255, 0.06)';
        }

        const alasanList = document.getElementById('intra-alasan');
        alasanList.innerHTML = data.alasan.map(a => `<li>${a}</li>`).join('');

        const metricsGrid = document.getElementById('intra-metrics');
        metricsGrid.innerHTML = `
            <div class="metric-item">
                <span class="metric-label">Buy Pressure</span>
                <span class="metric-value text-green">${data.buy_pressure.toFixed(1)}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Sell Pressure</span>
                <span class="metric-value text-red">${data.sell_pressure.toFixed(1)}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Intraday Gap</span>
                <span class="metric-value ${data.avg_gap >= 0 ? 'text-green' : 'text-red'}">${data.avg_gap >= 0 ? '+' : ''}${data.avg_gap.toFixed(2)}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Vol Ratio</span>
                <span class="metric-value">${data.vol_ratio.toFixed(2)}x</span>
            </div>
        `;
    }

    function renderFibonacci(fib, currentPrice) {
        const container = document.getElementById('fibonacci-levels');
        if (!fib || fib.fib_100 === 0) {
            container.innerHTML = `<p class="text-muted">Data Fibonacci tidak tersedia.</p>`;
            return;
        }

        const low = fib.fib_0;
        const high = fib.fib_100;
        const range = high - low;
        
        const levels = [
            { key: 'fib_100', label: '100% (High)' },
            { key: 'fib_786', label: '78.6%' },
            { key: 'fib_618', label: '61.8%' },
            { key: 'fib_50',  label: '50.0% (Pivot)' },
            { key: 'fib_382', label: '38.2%' },
            { key: 'fib_236', label: '23.6%' },
            { key: 'fib_0',   label: '0% (Low)' }
        ];
        
        let fibHTML = '';
        levels.forEach(lvl => {
            const price = fib[lvl.key];
            const valPct = range > 0 ? ((price - low) / range) * 100 : 0;
            
            // Highlight near levels (within 1.0% margin)
            const isNear = Math.abs(currentPrice - price) / price <= 0.01;
            const borderStyle = isNear ? 'style="border-left: 3px solid var(--accent-yellow); background: rgba(245, 158, 11, 0.06);"' : '';
            const nearLabel = isNear ? ' <span class="text-yellow" style="font-size: 8px; font-weight: 800; margin-left: 6px; padding: 1px 4px; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 3px; background: rgba(245, 158, 11, 0.05);">DEKAT HARGA</span>' : '';
            
            fibHTML += `
                <div class="fib-bar-item" ${borderStyle}>
                    <span class="fib-level-label">${lvl.label}${nearLabel}</span>
                    <div class="fib-progress-bg">
                        <div class="fib-progress-fill" style="width: ${valPct}%"></div>
                    </div>
                    <span class="fib-price">Rp ${Math.round(price).toLocaleString('id-ID')}</span>
                </div>
            `;
        });
        
        container.innerHTML = fibHTML;
    }

    function renderSupportResistance(data) {
        const formatRp = (val) => val ? `Rp ${val.toLocaleString('id-ID')}` : '-';
        
        document.getElementById('sr-r3').textContent = formatRp(data.r3);
        document.getElementById('sr-r2').textContent = formatRp(data.r2);
        document.getElementById('sr-r1').textContent = formatRp(data.r1);
        
        document.getElementById('sr-pivot').textContent = formatRp(data.pivot);
        
        document.getElementById('sr-s1').textContent = formatRp(data.s1);
        document.getElementById('sr-s2').textContent = formatRp(data.s2);
        document.getElementById('sr-s3').textContent = formatRp(data.s3);
    }

    function renderOrderBook(data) {
        if (!data || !data.volume_profile) return;
        
        // POC and Value Area stats
        const statsEl = document.getElementById('vp-stats');
        const formatRp = (val) => val ? `Rp ${Math.round(val).toLocaleString('id-ID')}` : '-';
        statsEl.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-item">
                    <span class="metric-label">POC (Point of Control)</span>
                    <span class="metric-value text-yellow">${formatRp(data.poc)}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Value Area High</span>
                    <span class="metric-value">${formatRp(data.value_area_high)}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Value Area Low</span>
                    <span class="metric-value">${formatRp(data.value_area_low)}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Harga Saat Ini</span>
                    <span class="metric-value">${formatRp(data.current_price)}</span>
                </div>
            </div>
        `;
        
        // Volume Profile bars
        const vpContainer = document.getElementById('ob-volume-profile');
        if (data.volume_profile && data.volume_profile.length > 0) {
            const maxVPVol = Math.max(...data.volume_profile.map(v => v.volume), 1);
            vpContainer.innerHTML = data.volume_profile.map(vp => {
                const pct = (vp.volume / maxVPVol) * 100;
                const isPOC = data.poc && Math.abs(vp.price - data.poc) < 1;
                return `
                    <div class="ob-vp-row">
                        <span class="ob-vp-price">${Math.round(vp.price).toLocaleString('id-ID')}</span>
                        <div class="ob-vp-bar-bg">
                            <div class="ob-vp-bar-fill ${vp.is_high_volume ? 'high-volume' : ''} ${isPOC ? 'poc-level' : ''}" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    function renderCompanyProfile(summary) {
        document.getElementById('company-summary').textContent = summary;
    }

    function formatTimeAgo(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            if (diffMins < 1) return 'Baru saja';
            if (diffMins < 60) return `${diffMins} menit lalu`;
            if (diffHours < 24) return `${diffHours} jam lalu`;
            if (diffDays === 1) return 'Kemarin';
            if (diffDays < 7) return `${diffDays} hari lalu`;
            if (diffDays < 30) return `${Math.floor(diffDays / 7)} minggu lalu`;
            return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
        } catch (e) {
            return '';
        }
    }

    function renderNews(newsData) {
        const container = document.getElementById('news-container');
        const statsContainer = document.getElementById('news-sentiment-stats');
        
        if (!newsData) {
            if (statsContainer) statsContainer.style.display = 'none';
            container.innerHTML = `<p class="text-muted">Tidak ada kabar terbaru yang ditemukan.</p>`;
            return;
        }

        // Handle both format (flat array or new structured dictionary)
        const articles = Array.isArray(newsData) ? newsData : (newsData.articles || []);
        
        if (articles.length === 0) {
            if (statsContainer) statsContainer.style.display = 'none';
            container.innerHTML = `<p class="text-muted">Tidak ada kabar terbaru yang ditemukan.</p>`;
            return;
        }

        // Render articles with premium layout
        container.innerHTML = articles.map(item => {
            const sentimentClass = item.sentiment ? item.sentiment.toLowerCase() : 'netral';
            const scoreLabel = item.score !== undefined ? `${item.score >= 0 ? '+' : ''}${item.score}` : '';
            const scoreBadge = scoreLabel ? `<span class="news-score-badge">${scoreLabel}</span>` : '';
            const timeAgo = formatTimeAgo(item.published_date);
            const timeHtml = timeAgo ? `<span class="news-timestamp">${timeAgo}</span>` : '';
            
            // Publisher favicon from source domain
            const sourceDomain = item.source_domain || '';
            const pubFavicon = sourceDomain 
                ? `<img class="news-pub-favicon" src="https://www.google.com/s2/favicons?domain=${sourceDomain}&sz=32" alt="" onerror="this.style.display='none'">` 
                : '';
            
            return `
                <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="news-item sentiment-border-${sentimentClass}">
                    <div class="news-item-header">
                        <div class="news-pub-info">
                            ${pubFavicon}
                            <span class="news-publisher">${item.publisher}</span>
                        </div>
                        <div class="news-sentiment-badges">
                            ${scoreBadge}
                            <span class="sentiment-badge sentiment-${sentimentClass}">${item.sentiment || 'NETRAL'}</span>
                        </div>
                    </div>
                    <p class="news-title">${item.title}</p>
                    <div class="news-item-footer">
                        ${timeHtml}
                        ${sourceDomain ? `<span class="news-source-domain">${sourceDomain}</span>` : ''}
                    </div>
                </a>
            `;
        }).join('');

        // Render statistics if available
        if (statsContainer && !Array.isArray(newsData)) {
            statsContainer.style.display = 'block';
            
            const sentimentIndex = newsData.sentiment_index !== undefined ? newsData.sentiment_index : 50;
            const avgScore = newsData.average_score !== undefined ? newsData.average_score : 0.0;
            const posCount = newsData.pos_count !== undefined ? newsData.pos_count : 0;
            const neuCount = newsData.neu_count !== undefined ? newsData.neu_count : 0;
            const negCount = newsData.neg_count !== undefined ? newsData.neg_count : 0;
            const skorNews = newsData.skor_news !== undefined ? newsData.skor_news : 0;
            
            // Dynamic color for sentiment index gauge
            const indexEl = document.getElementById('sentiment-index-pct');
            indexEl.textContent = `${sentimentIndex}%`;
            if (sentimentIndex >= 65) {
                indexEl.style.color = 'var(--accent-green)';
                indexEl.style.textShadow = '0 0 15px rgba(16, 185, 129, 0.3)';
            } else if (sentimentIndex <= 35) {
                indexEl.style.color = 'var(--accent-red)';
                indexEl.style.textShadow = '0 0 15px rgba(244, 63, 94, 0.3)';
            } else {
                indexEl.style.color = 'var(--accent-yellow)';
                indexEl.style.textShadow = '0 0 15px rgba(245, 158, 11, 0.3)';
            }
            
            document.getElementById('sentiment-avg-score').textContent = `${avgScore >= 0 ? '+' : ''}${avgScore.toFixed(2)}`;
            
            // Update Average Score styling
            const avgScoreEl = document.getElementById('sentiment-avg-score');
            avgScoreEl.className = 'sentiment-avg-score-val';
            if (avgScore > 0.2) avgScoreEl.style.color = 'var(--accent-green)';
            else if (avgScore < -0.2) avgScoreEl.style.color = 'var(--accent-red)';
            else avgScoreEl.style.color = '#ffffff';
            
            // Update recommendation box
            const recEl = document.getElementById('sentiment-news-skor');
            let recText = 'Netral (+0)';
            let recClass = 'badge-neutral';
            if (skorNews === 2) {
                recText = 'Sangat Bullish (+2)';
                recClass = 'badge-strong-bullish';
            } else if (skorNews === 1) {
                recText = 'Bullish (+1)';
                recClass = 'badge-bullish';
            } else if (skorNews === -1) {
                recText = 'Bearish (-1)';
                recClass = 'badge-bearish';
            } else if (skorNews === -2) {
                recText = 'Sangat Bearish (-2)';
                recClass = 'badge-strong-bearish';
            }
            recEl.textContent = recText;
            recEl.className = `sentiment-skor-badge ${recClass}`;
            
            // Update pills
            document.getElementById('sentiment-count-pos').textContent = posCount;
            document.getElementById('sentiment-count-neu').textContent = neuCount;
            document.getElementById('sentiment-count-neg').textContent = negCount;
            
            // Update progress bar fill
            const fillEl = document.getElementById('sentiment-progress-fill');
            if (fillEl) {
                fillEl.style.width = `${sentimentIndex}%`;
                if (sentimentIndex >= 65) {
                    fillEl.style.background = 'linear-gradient(90deg, var(--accent-yellow) 0%, var(--accent-green) 100%)';
                } else if (sentimentIndex <= 35) {
                    fillEl.style.background = 'linear-gradient(90deg, var(--accent-red) 0%, var(--accent-yellow) 100%)';
                } else {
                    fillEl.style.background = 'linear-gradient(90deg, var(--accent-red) 0%, var(--accent-yellow) 50%, var(--accent-green) 100%)';
                }
            }
        } else if (statsContainer) {
            statsContainer.style.display = 'none';
        }
    }

    function renderPCA(pcaData) {
        if (!pcaData) return;
        
        const scoreVal = pcaData.score !== undefined ? (pcaData.score > 0 ? `+${pcaData.score}` : pcaData.score) : '-';
        document.getElementById('pca-score').textContent = scoreVal;
        
        const gradeEl = document.getElementById('pca-grade');
        if (gradeEl) {
            gradeEl.textContent = pcaData.grade || '-';
            gradeEl.className = 'badge-tag';
            if (pcaData.color === 'green') gradeEl.classList.add('badge-strong-bullish');
            else if (pcaData.color === 'blue') gradeEl.classList.add('badge-bullish');
            else if (pcaData.color === 'red') gradeEl.classList.add('badge-strong-bearish');
            else gradeEl.classList.add('badge-neutral');
        }
        
        document.getElementById('eva-value').textContent = pcaData.eva_value || '-';
        document.getElementById('wacc-value').textContent = pcaData.wacc || '-';
        
        const tbody = document.getElementById('pca-indicators-tbody');
        if (tbody && pcaData.indicators) {
            tbody.innerHTML = '';
            pcaData.indicators.forEach(ind => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid rgba(255,255,255,0.02)';
                
                const zColor = ind.z_score >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
                const zSign = ind.z_score > 0 ? '+' : '';
                
                tr.innerHTML = `
                    <td style="padding: 6px 4px; color: var(--text-secondary); max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${ind.name}">${ind.name}</td>
                    <td style="padding: 6px 4px; text-align: right; font-family: monospace; color: #fff;">${ind.value}</td>
                    <td style="padding: 6px 4px; text-align: right; font-family: monospace; color: ${zColor}; font-weight: bold;">${zSign}${ind.z_score}</td>
                    <td style="padding: 6px 4px; text-align: right; font-family: monospace; color: var(--text-muted);">${ind.weight}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    function renderStatisticalArbitrage(arbData, ticker) {
        const card = document.getElementById('pairs-trading-card');
        if (!card) return;
        
        if (!arbData || arbData.peer === 'N/A') {
            card.style.display = 'none';
            return;
        }
        
        card.style.display = 'block';
        
        const cleanTicker = ticker.replace('.JK', '').replace('.jk', '').toUpperCase();
        
        // Cointegration status
        const cointBadge = document.getElementById('pairs-cointegrated-badge');
        if (cointBadge) {
            if (arbData.cointegrated) {
                cointBadge.textContent = 'TERKONFIRMASI (p-val < 0.05)';
                cointBadge.className = 'badge badge-strong-bullish';
            } else {
                cointBadge.textContent = `TIDAK TERKONFIRMASI (p-val: ${arbData.p_value})`;
                cointBadge.className = 'badge badge-neutral';
            }
        }
        
        // Asset Labels
        document.getElementById('pairs-asset-a').textContent = cleanTicker;
        document.getElementById('pairs-asset-b').textContent = arbData.peer;
        
        // Stats
        document.getElementById('pairs-hedge-ratio').textContent = arbData.hedge_ratio;
        document.getElementById('pairs-intercept').textContent = arbData.intercept;
        document.getElementById('pairs-p-value').textContent = arbData.p_value;
        document.getElementById('pairs-equation-str').textContent = `log(${cleanTicker}) - ${arbData.hedge_ratio}*log(${arbData.peer})`;
        
        // Z-score
        const zScore = arbData.z_score;
        document.getElementById('pairs-z-score').textContent = zScore > 0 ? `+${zScore.toFixed(2)}` : zScore.toFixed(2);
        
        const devBadge = document.getElementById('pairs-zscore-deviation');
        if (devBadge) {
            devBadge.textContent = arbData.label === 1 ? 'Undervalued A' : 
                                  arbData.label === 2 ? 'Undervalued B' : 
                                  arbData.label === 3 ? 'Mean Reversion' : 
                                  arbData.label === 4 ? 'Decoupling Alert' : 'Normal';
            devBadge.className = 'badge-tag';
            if (arbData.label === 1 || arbData.label === 2) {
                devBadge.classList.add('badge-strong-bullish');
            } else if (arbData.label === 4) {
                devBadge.classList.add('badge-strong-bearish');
            } else {
                devBadge.classList.add('badge-neutral');
            }
        }
        
        // Standard GARCH Instruction
        const garchSignal = document.getElementById('pairs-execution-signal');
        garchSignal.textContent = arbData.instruction;
        garchSignal.className = 'pairs-signal-badge';
        if (arbData.label === 1 || arbData.label === 2) {
            garchSignal.style.background = 'var(--accent-green)';
            garchSignal.style.color = '#fff';
        } else if (arbData.label === 4) {
            garchSignal.style.background = 'var(--accent-red)';
            garchSignal.style.color = '#fff';
        } else {
            garchSignal.style.background = 'rgba(255,255,255,0.1)';
            garchSignal.style.color = '#fff';
        }
        
        document.getElementById('pairs-explanation').textContent = arbData.explanation;
        
        // LSTM AI bindings
        const lstmSignal = document.getElementById('lstm-execution-signal');
        lstmSignal.textContent = arbData.lstm_instruction;
        if (arbData.lstm_predicted_label === 1 || arbData.lstm_predicted_label === 2) {
            lstmSignal.style.background = '#10b981';
            lstmSignal.style.boxShadow = '0 4px 10px rgba(16, 185, 129, 0.3)';
        } else if (arbData.lstm_predicted_label === 4) {
            lstmSignal.style.background = '#f43f5e';
            lstmSignal.style.boxShadow = '0 4px 10px rgba(244, 63, 94, 0.3)';
        } else if (arbData.lstm_predicted_label === 3) {
            lstmSignal.style.background = '#3b82f6';
            lstmSignal.style.boxShadow = '0 4px 10px rgba(59, 130, 246, 0.3)';
        } else {
            lstmSignal.style.background = '#f59e0b';
            lstmSignal.style.boxShadow = '0 4px 10px rgba(245, 158, 11, 0.3)';
        }
        
        const lstmExplain = document.getElementById('lstm-explanation');
        let lstmExpStr = `Model LSTM 20-hari mendeteksi pola nonlinear spread. `;
        if (arbData.lstm_predicted_label === 1) lstmExpStr += `AI merekomendasikan Akumulasi Aset A (${cleanTicker}) karena peluang profit rebound yang tinggi.`;
        else if (arbData.lstm_predicted_label === 2) lstmExpStr += `AI merekomendasikan Akumulasi Aset B (${arbData.peer}) karena peluang profit rebound yang tinggi.`;
        else if (arbData.lstm_predicted_label === 3) lstmExpStr += `Spread telah kembali mendekati rata-rata (mean reversion). Ambil profit penuh.`;
        else if (arbData.lstm_predicted_label === 4) lstmExpStr += `AI mendeteksi anomali decoupling ekstrem. Segera eksekusi Stop-Loss untuk proteksi modal.`;
        else lstmExpStr += `Spread bergerak stabil di area ekuilibrium normal. Standby / Tahan posisi.`;
        lstmExplain.textContent = lstmExpStr;
        
        // LSTM Probs
        const probsDiv = document.getElementById('lstm-prob-bars');
        if (probsDiv && arbData.lstm_probabilities) {
            probsDiv.innerHTML = '';
            const labels = ["Hold (L0)", "Beli A (L1)", "Beli B (L2)", "Exit (L3)", "Stop Loss (L4)"];
            const bgColors = ["#f59e0b", "#10b981", "#ec4899", "#3b82f6", "#f43f5e"];
            
            arbData.lstm_probabilities.forEach((prob, idx) => {
                const label = labels[idx];
                const color = bgColors[idx];
                
                const item = document.createElement('div');
                item.style.display = 'flex';
                item.style.alignItems = 'center';
                item.style.gap = '8px';
                item.style.width = '100%';
                
                item.innerHTML = `
                    <span style="width: 75px; color: var(--text-secondary); text-align: left; font-size: 10px;">${label}</span>
                    <div style="flex-grow: 1; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; position: relative;">
                        <div style="position: absolute; left: 0; top: 0; bottom: 0; width: ${prob}%; background: ${color}; border-radius: 3px; transition: width 0.6s ease-out;"></div>
                    </div>
                    <span style="width: 32px; text-align: right; font-family: monospace; color: #fff; font-size: 10px; font-weight: bold;">${prob}%</span>
                `;
                probsDiv.appendChild(item);
            });
        }
        
        // Pointer Pin position
        const pointer = document.getElementById('zscore-pointer-pin');
        const pointerVal = document.getElementById('pointer-value-label');
        if (pointer && pointerVal) {
            const pct = Math.min(100, Math.max(0, ((zScore + 3) / 6) * 100));
            pointer.style.left = `${pct}%`;
            pointerVal.textContent = (zScore > 0 ? '+' : '') + zScore.toFixed(2);
        }
        
        // Render Sparkline
        const sparkCanvas = document.getElementById('pairs-sparkline-canvas');
        if (sparkCanvas && arbData.spread_history && arbData.spread_history.length > 0) {
            sparkCanvas.innerHTML = '';
            const history = arbData.spread_history;
            const minH = Math.min(...history);
            const maxH = Math.max(...history);
            const range = maxH - minH || 1;
            
            history.forEach(v => {
                const bar = document.createElement('div');
                bar.className = 'spark-bar';
                const heightPct = Math.min(100, Math.max(10, ((v - minH) / range) * 100));
                
                bar.style.flexGrow = '1';
                bar.style.height = `${heightPct}%`;
                bar.style.borderRadius = '3px 3px 0 0';
                
                if (v >= 0) {
                    bar.style.background = 'linear-gradient(to top, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.8))';
                    bar.style.boxShadow = '0 0 4px rgba(16, 185, 129, 0.3)';
                } else {
                    bar.style.background = 'linear-gradient(to top, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.8))';
                    bar.style.boxShadow = '0 0 4px rgba(59, 130, 246, 0.3)';
                }
                
                bar.style.transition = 'height 0.8s ease-in-out';
                bar.title = `Residual: ${v.toFixed(4)}`;
                
                sparkCanvas.appendChild(bar);
            });
        }
    }

    function renderCrashMomentum(crashData) {
        const card = document.getElementById('crash-momentum-card');
        if (!card) return;
        
        if (!crashData) {
            card.style.display = 'none';
            return;
        }
        
        card.style.display = 'block';
        
        // Badge Signal
        const badge = document.getElementById('crash-signal-badge');
        if (badge) {
            badge.textContent = crashData.signal;
            badge.className = 'badge';
            if (crashData.signal.includes('WARNING')) {
                badge.className = 'badge badge-strong-bearish';
            } else if (crashData.signal.includes('BUY')) {
                badge.className = 'badge badge-strong-bullish';
            } else {
                badge.className = 'badge badge-neutral';
            }
        }
        
        // Gauge Probability
        const prob = crashData.ex_ante_crash_probability;
        const gaugeScore = document.getElementById('crash-gauge-score');
        const gaugeProgress = document.getElementById('crash-gauge-progress');
        
        if (gaugeScore) gaugeScore.textContent = `${prob.toFixed(1)}%`;
        if (gaugeProgress) {
            gaugeProgress.setAttribute('stroke-dasharray', `${prob}, 100`);
            if (prob >= 70.0) {
                gaugeProgress.setAttribute('stroke', '#f43f5e'); // Red glow
            } else if (prob >= 40.0) {
                gaugeProgress.setAttribute('stroke', '#fbbf24'); // Yellow/Amber glow
            } else {
                gaugeProgress.setAttribute('stroke', '#10b981'); // Green glow
            }
        }
        
        // Stats
        document.getElementById('crash-max-dd').textContent = `${crashData.max_drawdown.toFixed(2)}%`;
        document.getElementById('crash-skewness').textContent = crashData.skewness.toFixed(3);
        document.getElementById('crash-kurtosis').textContent = crashData.excess_kurtosis.toFixed(3);
        
        // Action & Instruction
        const instTitle = document.getElementById('crash-instruction-title');
        if (instTitle) {
            instTitle.textContent = crashData.instruction;
            if (crashData.signal.includes('WARNING')) {
                instTitle.style.color = 'var(--accent-red)';
            } else if (crashData.signal.includes('BUY')) {
                instTitle.style.color = 'var(--accent-green)';
            } else {
                instTitle.style.color = '#fff';
            }
        }
        
        // Pills
        document.getElementById('pill-vol-ratio').textContent = `Vol Ratio: ${crashData.volatility_ratio.toFixed(2)}`;
        document.getElementById('pill-vol-spike').textContent = `Vol Spike: ${crashData.volume_spike_ratio.toFixed(2)}`;
        document.getElementById('pill-rsi-current').textContent = `RSI: ${crashData.rsi_current.toFixed(1)}`;
        
        // Reasons
        const reasonsList = document.getElementById('crash-reasons-list');
        if (reasonsList && crashData.reasons) {
            reasonsList.innerHTML = crashData.reasons.map(reason => `<li>${reason}</li>`).join('');
        }
    }

    function renderHybridForecast(hybridData) {
        const card = document.getElementById('hybrid-forecast-card');
        if (!card) return;
        
        if (!hybridData) {
            card.style.display = 'none';
            return;
        }
        
        card.style.display = 'block';
        
        // Direction
        const dirEl = document.getElementById('hybrid-direction');
        const dirBadge = document.getElementById('hybrid-direction-badge');
        const dirBox = document.getElementById('hybrid-dir-box');
        
        const direction = hybridData.direction || 'SIDEWAYS';
        dirEl.textContent = direction;
        dirBadge.textContent = direction;
        
        if (direction === 'BULLISH') {
            dirEl.style.color = 'var(--accent-green)';
            dirEl.textContent = 'BULLISH 🚀';
            dirBadge.className = 'hybrid-badge badge-strong-bullish';
            dirBadge.style.background = 'rgba(16, 185, 129, 0.15)';
            dirBadge.style.color = 'var(--accent-green)';
            dirBox.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            dirBox.style.background = 'rgba(16, 185, 129, 0.05)';
        } else if (direction === 'BEARISH') {
            dirEl.style.color = 'var(--accent-red)';
            dirEl.textContent = 'BEARISH 📉';
            dirBadge.className = 'hybrid-badge badge-strong-bearish';
            dirBadge.style.background = 'rgba(244, 63, 94, 0.15)';
            dirBadge.style.color = 'var(--accent-red)';
            dirBox.style.border = '1px solid rgba(244, 63, 94, 0.3)';
            dirBox.style.background = 'rgba(244, 63, 94, 0.05)';
        } else {
            dirEl.style.color = 'var(--accent-yellow)';
            dirEl.textContent = 'SIDEWAYS ↔️';
            dirBadge.className = 'hybrid-badge badge-neutral';
            dirBadge.style.background = 'rgba(245, 158, 11, 0.15)';
            dirBadge.style.color = 'var(--accent-yellow)';
            dirBox.style.border = '1px solid rgba(245, 158, 11, 0.3)';
            dirBox.style.background = 'rgba(245, 158, 11, 0.05)';
        }
        
        // Target Prices
        document.getElementById('hybrid-pred-price').textContent = hybridData.predicted_price ? `Rp ${hybridData.predicted_price.toLocaleString('id-ID')}` : 'Rp 0';
        document.getElementById('hybrid-high-target').textContent = hybridData.expected_high ? `Rp ${hybridData.expected_high.toLocaleString('id-ID')}` : 'Rp 0';
        document.getElementById('hybrid-low-target').textContent = hybridData.expected_low ? `Rp ${hybridData.expected_low.toLocaleString('id-ID')}` : 'Rp 0';
        
        // Confidence score
        const conf = hybridData.confidence || 50.0;
        document.getElementById('hybrid-gauge-score').textContent = `${conf.toFixed(1)}%`;
        
        const progress = document.getElementById('hybrid-gauge-progress');
        if (progress) {
            progress.setAttribute('stroke-dasharray', `${conf}, 100`);
            if (conf >= 75.0) {
                progress.setAttribute('stroke', '#10b981'); // Green glow
            } else if (conf >= 60.0) {
                progress.setAttribute('stroke', '#3b82f6'); // Blue glow
            } else {
                progress.setAttribute('stroke', '#fbbf24'); // Yellow glow
            }
        }
        
        // GA optimization details
        document.getElementById('hybrid-best-chromosome').textContent = hybridData.best_chromosome || 'N/A';
        document.getElementById('hybrid-fitness-score').textContent = hybridData.ga_fitness ? hybridData.ga_fitness.toFixed(2) : '0.00';
        
        // Performance metrics
        if (hybridData.metrics) {
            document.getElementById('hybrid-rev-boost').textContent = hybridData.metrics.annualized_revenue_boost || '+35.16%';
            document.getElementById('hybrid-win-boost').textContent = hybridData.metrics.win_rate_boost || '+15.22%';
        }
    }

    function renderUMAShield(umaData) {
        const shield = document.getElementById('uma-shield');
        const prob = document.getElementById('uma-prob');
        const reasons = document.getElementById('uma-reasons');
        
        if (!shield) return;
        
        if (umaData && umaData.detected) {
            shield.style.display = 'flex';
            if (prob) prob.textContent = `${umaData.probability}%`;
            if (reasons) {
                reasons.textContent = umaData.reasons ? umaData.reasons.join(' | ') : 'Terdeteksi anomali volume & volatilitas jangka pendek secara ekstrem.';
            }
        } else {
            shield.style.display = 'none';
        }
    }

    function renderMeanReversionOU(ouData) {
        const speedEl = document.getElementById('ou-speed-a');
        const hlEl = document.getElementById('ou-half-life');
        const levelEl = document.getElementById('ou-mean-level');
        const statusEl = document.getElementById('ou-status');
        
        if (!ouData) return;
        
        if (speedEl) {
            speedEl.textContent = ouData.speed_a ? ouData.speed_a.toFixed(4) : '0.0000';
        }
        if (hlEl) {
            hlEl.textContent = typeof ouData.half_life_days === 'number' ? `${ouData.half_life_days.toFixed(1)} Hari` : ouData.half_life_days;
        }
        if (levelEl) {
            levelEl.textContent = ouData.mean_level ? `Rp ${ouData.mean_level.toLocaleString('id-ID')}` : 'Rp -';
        }
        if (statusEl) {
            statusEl.textContent = ouData.status || 'Normal';
            if (ouData.status === 'Mean Reverting') {
                statusEl.className = 'badge-tag text-green';
                statusEl.style.background = 'rgba(16, 185, 129, 0.1)';
            } else {
                statusEl.className = 'badge-tag text-yellow';
                statusEl.style.background = 'rgba(245, 158, 11, 0.1)';
            }
        }
    }

    function renderTradingViewChart(ticker) {
        const baseTicker = ticker.replace('.JK', '').toUpperCase();
        const symbol = ticker.endsWith('.JK') ? `IDX:${baseTicker}` : baseTicker;
        
        const chartContainer = document.getElementById('tradingview-chart-container');
        chartContainer.innerHTML = `<div id="tradingview_chart" style="height: 460px; width: 100%;"></div>`;
        
        if (!window.TradingView) {
            const script = document.createElement('script');
            script.src = 'https://s3.tradingview.com/tv.js';
            script.type = 'text/javascript';
            script.onload = () => {
                try {
                    new TradingView.widget({
                        "width": "100%",
                        "height": 460,
                        "symbol": symbol,
                        "interval": "D",
                        "timezone": "Asia/Jakarta",
                        "theme": "dark",
                        "style": "1",
                        "locale": "id",
                        "toolbar_bg": "#131b2e",
                        "enable_publishing": false,
                        "hide_side_toolbar": false,
                        "allow_symbol_change": true,
                        "container_id": "tradingview_chart"
                    });
                } catch (e) {
                    console.error("Gagal memuat TradingView widget:", e);
                }
            };
            document.head.appendChild(script);
        } else {
            try {
                new TradingView.widget({
                    "width": "100%",
                    "height": 460,
                    "symbol": symbol,
                    "interval": "D",
                    "timezone": "Asia/Jakarta",
                    "theme": "dark",
                    "style": "1",
                    "locale": "id",
                    "toolbar_bg": "#131b2e",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "container_id": "tradingview_chart"
                });
            } catch (e) {
                console.error("Gagal memuat TradingView widget:", e);
            }
        }
    }

    function startPricePooling(ticker) {
        if (liveTickerInterval) {
            clearInterval(liveTickerInterval);
        }
        
        liveTickerInterval = setInterval(async () => {
            try {
                const cleanTicker = ticker.replace('.JK', '').replace('.jk', '').toUpperCase();
                const response = await fetch(`/api/price/${cleanTicker}`);
                if (response.ok) {
                    const priceData = await response.json();
                    
                    const priceEl = document.getElementById('stock-price');
                    const changeEl = document.getElementById('stock-change');
                    
                    if (priceEl && priceData.price) {
                        const formattedPrice = `Rp ${priceData.price.toLocaleString('id-ID')}`;
                        if (priceEl.textContent !== formattedPrice) {
                            priceEl.textContent = formattedPrice;
                            
                            // Micro-animation: subtle neon flash of mint green
                            priceEl.classList.add('price-flash');
                            setTimeout(() => {
                                priceEl.classList.remove('price-flash');
                            }, 500);
                        }
                    }
                    
                    if (changeEl && priceData.change_pct !== undefined) {
                        const change = priceData.change_pct;
                        changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`;
                        changeEl.className = `price-change ${change >= 0 ? 'text-green' : 'text-red'}`;
                    }
                }
            } catch (e) {
                console.error("Gagal melakukan pooling harga real-time:", e);
            }
        }, 8000); // Poll every 8 seconds
    }
});
