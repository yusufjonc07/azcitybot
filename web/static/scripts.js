const testimonials = [
            {
                name: 'Saida Khaitmatova',
                role: 'Customer',
                avatar: 'assets/clients/saida.png',
                rating: 5,
                text: 'Muomila 👍🏻 - qoshimcha kirish chiqish bo’yicha savollaga erinmiy javob berishligisi. Halal food ✅ - o’zligisi etmiy registratsiya qilishganidan judayam hursan bo’gandim samalyotda. Check in ✅ - oyna tomonidan. Shu uchta xizmatlari bilan rosa yoqgan, shundan beri boshqa avia kassalaga qiziqmiy to’g’ridan to’g’ri Bulani xizmatidan foydalanaman va hammaga tavsiya qilaman.'
            },
            {
                name: 'Ismail Asrorov',
                role: 'Customer',
                avatar: 'assets/clients/ismail.png',
                rating: 5,
                text: 'Har safar samolyotga chiqqanimda bir shunaqa post qo\'yaman deb o\'ylardim, yana esdan chiqib ketardi. Haqiqatdan servis ajoyib! Ayniqsa, aytmasa ham halal meal ga reg qibergan payt samolyotda hammadan oldin bizga taom opkeganda xursand bop ketadi odam. Juda ko\'p marta bilet olib ko\'rdik. Har safar servisdan mamnun bo\'ldik. Alloh barakasini bersin.'
            },
            {
                name: 'Kurambaeva Dilfuza',
                role: 'Customer',
                avatar: 'assets/clients/dilfuza.png',
                rating: 5,
                text: 'Men ham qo\'shilaman. Aeroportda turib telefon qilganimda bittada javob bergan, joyida tushunmovchilikni hal qilib bergan! 💯💯💯'
            },
            {
                name: 'Rahmatulloh Rahmonov',
                role: 'Customer',
                avatar: 'assets/clients/rahmatulloh.png',
                rating: 5,
                text: 'Menam bulardan 4 yildan beri bilet olaman (taxminan 4 marta olganman). Narxni insof bilan qo\'yishadi. Haqiqatdan muomalasi o\'rnak olsa arziydi.'
            },
            {
                name: 'Ravshan Mirzo',
                role: 'Customer',
                avatar: 'assets/clients/ravshan.png',
                rating: 5,
                text: 'Koreyaga qaytish biletimni 3 marta o\'zgartirdim, bir og\'iz oshiqcha gapsiz erinmasdan qiberdi akamiz. Baraka topsin Zuhriddin AZCity.'
            },
            {
                name: 'Mushtariybegim Alieva',
                role: 'Customer',
                avatar: 'assets/clients/mushtariy.png',
                rating: 5,
                text: 'Telegramda ham javob juda tez keladi, gap yo’q servisga 👌'
            }
        ];


        const stats = [
            { value: '7 Years', label: 'Experience' },
            { value: '99.9%', label: 'Retention Rate' },
            { value: '10K+', label: 'Happy Travelers' },
            { value: '20,610', label: 'Tickets Sold' }
        ];

        const gallery = [
            { src: 'assets/gallery/20251119_092028.jpg', alt: 'Workspace view 1', size: 'large' },
            // { src: 'assets/gallery/20251215_092845.jpg', alt: 'Workspace view 2', size: 'small' },
            // { src: 'assets/gallery/20260213_075208.jpg', alt: 'Workspace view 3', size: 'small' },
            { src: 'assets/gallery/20260330_064136.jpg', alt: 'Workspace view 4', size: 'large' }
        ];

        function renderTestimonials() {
            const container = document.getElementById('testimonial-list');
            if (!container) return;

            container.innerHTML = testimonials.map((item) => `
                <div class="swiper-slide">
                    <article class="testimonial-card">
                        <img src="${item.avatar}" alt="${item.name}" class="testimonial-avatar" loading="lazy">
                        <div class="testimonial-rating">${Array.from({ length: 5 }, (_, index) => `<i class="fa${index < item.rating ? 's' : 'r'} fa-star"></i>`).join('')}</div>
                        <p class="testimonial-text">“${item.text}”</p>
                        <h3>${item.name}</h3>
                        <p class="testimonial-role">${item.role}</p>
                    </article>
                </div>
            `).join('');
        }

        function renderStats() {
            const container = document.getElementById('stats-list');
            if (!container) return;

            container.innerHTML = stats.map((item) => `
                <article class="stat-card">
                    <div class="stat-circle">
                        
                        <span class="stat-value" data-target="${item.value}">0</span>
                    </div>
                    <p class="stat-label">${item.label}</p>
                </article>
            `).join('');
        }

        function renderGallery() {
            const container = document.getElementById('gallery-list');
            if (!container) return;

            container.innerHTML = gallery.map((item) => `
                <figure class="gallery-item ${item.size === 'large' ? 'gallery-large' : 'gallery-small'}">
                    <img src="${item.src}" alt="${item.alt}" loading="lazy">
                </figure>
            `).join('');
        }

        function animateCounter(element) {
            const target = element.dataset.target;
            const match = target.match(/^(-?\d+(?:\.\d+)?)(.*)$/);
            if (!match) return;

            const numericValue = parseFloat(match[1]);
            const suffix = match[2] || '';
            const duration = 1400;
            const start = performance.now();

            const step = (timestamp) => {
                const progress = Math.min((timestamp - start) / duration, 1);
                const currentValue = numericValue * progress;
                const formattedValue = Number.isInteger(numericValue) ? Math.round(currentValue) : currentValue.toFixed(1);
                element.textContent = `${formattedValue}${suffix}`;

                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            };

            requestAnimationFrame(step);
        }

        function observeCounters() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.5 });

            document.querySelectorAll('.stat-value').forEach((item) => observer.observe(item));
        }

        renderTestimonials();
        renderStats();
        renderGallery();
        observeCounters();

        new Swiper('.locationSwiper', {
            direction: 'vertical',
            loop: true,
            autoplay: {
                delay: 3000,
                disableOnInteraction: false,
            },
            speed: 500,
        });

        new Swiper('.testimonial-swiper', {
            slidesPerView: 1.2,
            centeredSlides: true,
            spaceBetween: 24,
            loop: true,
            autoplay: {
                delay: 4000,
                disableOnInteraction: false,
            },
            breakpoints: {
                768: { slidesPerView: 2 },
                992: { slidesPerView: 2.2 }
            }
        });

        new Swiper('.company-swiper', {
            slideClass: 'company-card',
            slidesPerView: 'auto',
            spaceBetween: 16,
            loop: true,
            speed: 5000,
            allowTouchMove: false,
            autoplay: {
                delay: 0,
                disableOnInteraction: false,
                pauseOnMouseEnter: true,
            },
        });

        const translations = {
            uz: {
                'Home': 'Bosh sahifa', 'Partners': 'Hamkorlar', 'Testimonials': 'Mijozlar fikri', 'Contact': 'Aloqa', 'Book Now': 'Hoziroq band qiling', 'Get Advice': 'Maslahat oling', 'FAQ': 'Savollar', 'Support': 'Yordam',
                'Your trusted flight partner': 'Ishonchli parvoz hamkoringiz', 'Book Airline Tickets with Confidence': 'Aviabiletlarni ishonch bilan band qiling', 'We help you find the best flights, compare fares, and provide expert guidance for a smooth travel experience.': 'Eng yaxshi reyslarni topish, narxlarni solishtirish va qulay sayohat uchun maslahat beramiz.',
                'Expert flight consultations': 'Parvoz bo‘yicha ekspert maslahati', 'Fast, Reliable Flight Support': 'Tezkor va ishonchli parvoz yordami', 'From ticket booking to travel advice, we make planning your next flight simple, efficient, and stress-free.': 'Chipta band qilishdan sayohat maslahatigacha, keyingi parvozingizni oson va xotirjam rejalashtiramiz.',
                'Trusted by industry leaders': 'Sohadagi yetakchilar ishonchi', 'Top Airline Companies': 'Yetakchi aviakompaniyalar', 'What Clients Say About Us': 'Mijozlarimiz fikri', 'Trusted by Travelers': 'Sayohatchilar ishonchi', 'Our Impact in Numbers': 'Natijalarimiz raqamlarda', 'Our Workplace Gallery': 'Ofis galereyasi', 'Moments from Our Own Workspace': 'Ish joyimizdan lavhalar',
                'Ready when you are': 'Siz tayyor bo‘lganingizda', 'Let’s plan your next safe, smooth journey.': 'Keyingi xavfsiz va qulay sayohatingizni rejalashtiraylik.', 'From ticket reservations to practical advice, our team is here to help every step of the way.': 'Jamoamiz chipta band qilishdan amaliy maslahatlargacha har qadamda yordam beradi.', 'Contact Us': 'Biz bilan bog‘laning',
                'Your trusted partner for simple, safe, and seamless travel planning.': 'Oddiy, xavfsiz va qulay sayohat rejalashtirishdagi ishonchli hamkoringiz.', 'Explore': 'Sahifalar', 'Our Partners': 'Hamkorlarimiz', 'Services': 'Xizmatlar', 'Flight Reservations': 'Aviabilet band qilish', 'Travel Consultation': 'Sayohat maslahati', 'Customer Support': 'Mijozlarga yordam', 'Visit Us': 'Bizga tashrif buyuring',
                'Every day, 10:00 – 22:00': 'Har kuni, 10:00 – 22:00',
                'Get in touch': 'Bog‘lanish',
                '© 2025 AzCity Travel Agency. All rights reserved.': '© 2025 AzCity Travel Agency. Barcha huquqlar himoyalangan.',
                'Privacy Policy': 'Maxfiylik siyosati',
                'Terms of Service': 'Foydalanish shartlari'
            },
            ru: {
                'Home': 'Главная', 'Partners': 'Партнёры', 'Testimonials': 'Отзывы', 'Contact': 'Контакты', 'Book Now': 'Забронировать', 'Get Advice': 'Получить консультацию', 'FAQ': 'Вопросы', 'Support': 'Поддержка',
                'Your trusted flight partner': 'Ваш надёжный партнёр по перелётам', 'Book Airline Tickets with Confidence': 'Бронируйте авиабилеты с уверенностью', 'We help you find the best flights, compare fares, and provide expert guidance for a smooth travel experience.': 'Мы поможем найти лучшие рейсы, сравнить тарифы и сделаем путешествие комфортным.',
                'Expert flight consultations': 'Экспертные консультации по перелётам', 'Fast, Reliable Flight Support': 'Быстрая и надёжная поддержка', 'From ticket booking to travel advice, we make planning your next flight simple, efficient, and stress-free.': 'От бронирования билетов до советов по поездке — мы сделаем планирование простым и спокойным.',
                'Trusted by industry leaders': 'Нам доверяют лидеры отрасли', 'Top Airline Companies': 'Ведущие авиакомпании', 'What Clients Say About Us': 'Что говорят наши клиенты', 'Trusted by Travelers': 'Нам доверяют путешественники', 'Our Impact in Numbers': 'Наши результаты в цифрах', 'Our Workplace Gallery': 'Галерея офиса', 'Moments from Our Own Workspace': 'Моменты из нашего офиса',
                'Ready when you are': 'Когда вы готовы', 'Let’s plan your next safe, smooth journey.': 'Давайте спланируем ваше безопасное и комфортное путешествие.', 'From ticket reservations to practical advice, our team is here to help every step of the way.': 'Наша команда поможет на каждом этапе — от бронирования до практических советов.', 'Contact Us': 'Связаться с нами',
                'Your trusted partner for simple, safe, and seamless travel planning.': 'Ваш надёжный партнёр для простого, безопасного и комфортного планирования путешествий.', 'Explore': 'Навигация', 'Our Partners': 'Наши партнёры', 'Services': 'Услуги', 'Flight Reservations': 'Бронирование авиабилетов', 'Travel Consultation': 'Консультация по путешествиям', 'Customer Support': 'Поддержка клиентов', 'Visit Us': 'Посетите нас',
                'Every day, 10:00 – 22:00': 'Каждый день, 10:00 – 22:00',
                'Get in touch': 'Связаться',
                '© 2025 AzCity Travel Agency. All rights reserved.': '© 2025 AzCity Travel Agency. Все права защищены.',
                'Privacy Policy': 'Политика конфиденциальности',
                'Terms of Service': 'Условия использования'
            },
            ko: {
                'Home': '홈', 'Partners': '파트너', 'Testimonials': '고객 후기', 'Contact': '문의', 'Book Now': '지금 예약하기', 'Get Advice': '상담 받기', 'FAQ': '자주 묻는 질문', 'Support': '고객 지원',
                'Your trusted flight partner': '믿을 수 있는 항공 여행 파트너', 'Book Airline Tickets with Confidence': '안심하고 항공권을 예약하세요', 'We help you find the best flights, compare fares, and provide expert guidance for a smooth travel experience.': '최적의 항공편을 찾고 요금을 비교하며 편안한 여행을 위한 전문 안내를 제공합니다.',
                'Expert flight consultations': '전문 항공 상담', 'Fast, Reliable Flight Support': '빠르고 믿을 수 있는 항공 지원', 'From ticket booking to travel advice, we make planning your next flight simple, efficient, and stress-free.': '항공권 예약부터 여행 조언까지 다음 여행을 쉽고 편안하게 준비해 드립니다.',
                'Trusted by industry leaders': '업계 리더가 신뢰하는', 'Top Airline Companies': '주요 항공사', 'What Clients Say About Us': '고객 후기', 'Trusted by Travelers': '여행객이 신뢰하는', 'Our Impact in Numbers': '숫자로 보는 성과', 'Our Workplace Gallery': '사무실 갤러리', 'Moments from Our Own Workspace': '우리 공간의 순간들',
                'Ready when you are': '준비되셨을 때', 'Let’s plan your next safe, smooth journey.': '안전하고 편안한 다음 여행을 함께 계획해 보세요.', 'From ticket reservations to practical advice, our team is here to help every step of the way.': '항공권 예약부터 실용적인 조언까지 모든 단계에서 도와드립니다.', 'Contact Us': '문의하기',
                'Your trusted partner for simple, safe, and seamless travel planning.': '간편하고 안전하며 편안한 여행 계획을 위한 믿을 수 있는 파트너입니다.', 'Explore': '둘러보기', 'Our Partners': '파트너사', 'Services': '서비스', 'Flight Reservations': '항공권 예약', 'Travel Consultation': '여행 상담', 'Customer Support': '고객 지원', 'Visit Us': '방문 안내',
                'Every day, 10:00 – 22:00': '매일 10:00 – 22:00',
                'Get in touch': '문의하기',
                '© 2025 AzCity Travel Agency. All rights reserved.': '© 2025 AzCity Travel Agency. 모든 권리 보유.',
                'Privacy Policy': '개인정보 처리방침',
                'Terms of Service': '이용약관'
            }
        };

        const originalText = new WeakMap();

        // Collapse internal line-wrap whitespace (newlines/indentation from the
        // HTML source) down to single spaces so text nodes actually match the
        // translation dictionary keys.
        const normalize = (str) => str.replace(/\s+/g, ' ').trim();

        // Walk only real content text nodes: skip <script>, <style> and
        // <option> (language names in the picker should stay as-is).
        function collectTextNodes(root) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    const parentTag = node.parentElement && node.parentElement.tagName;
                    if (parentTag === 'SCRIPT' || parentTag === 'STYLE' || parentTag === 'OPTION') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
                }
            });
            const nodes = [];
            let current;
            while ((current = walker.nextNode())) nodes.push(current);
            return nodes;
        }

        const translatePage = (language) => {
            document.documentElement.lang = language;
            document.title = language === 'ko' ? 'AzCity - 여행사' : 'AzCity - Travel Agency';

            collectTextNodes(document.body).forEach((node) => {
                if (!originalText.has(node)) {
                    originalText.set(node, normalize(node.nodeValue));
                }
                const source = originalText.get(node);
                const translated = translations[language]?.[source] || source;
                const leading = node.nodeValue.match(/^\s*/)[0];
                const trailing = node.nodeValue.match(/\s*$/)[0];
                node.nodeValue = `${leading}${translated}${trailing}`;
            });

            localStorage.setItem('azcity-language', language);
        };

        const languageSelect = document.getElementById('language-select');
        languageSelect.value = localStorage.getItem('azcity-language') || 'en';
        translatePage(languageSelect.value);
        languageSelect.addEventListener('change', (event) => {
            translatePage(event.target.value);
        });