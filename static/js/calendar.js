document.addEventListener('DOMContentLoaded', () => {
    const selectors = {
        calendarEvents: 'calendar-events',
        eventsUrl: 'events-url',
        prevBtn: 'prev-btn',
        nextBtn: 'next-btn',
        datePicker: 'date-picker',
        masterFilter: 'master-filter',
        systemFilter: 'system-filter',
    };

    let currentPage = 1;
    const eventsPerPage = 3;
    let allEvents = [];

    const elements = {};
    Object.keys(selectors).forEach(key => {
        const selector = selectors[key];
        elements[key] = document.getElementById(selector) || document.querySelector(selector);
    });

    function fetchEvents() {
        const date = elements.datePicker.value;
        const master = elements.masterFilter.value;
        const system = elements.systemFilter.value;

        // Додаємо фільтри до URL запиту
        const url = new URL(elements.eventsUrl.dataset.url, window.location.origin);
        url.searchParams.append('page', currentPage);
        url.searchParams.append('limit', eventsPerPage);
        if (date) url.searchParams.append('date', date);
        if (master) url.searchParams.append('master', master);
        if (system) url.searchParams.append('system', system);
        console.log("Fetching events with URL:", url.toString());  // Додано для відладки

        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log("Fetched events:", data);  // Додано для відладки
                allEvents = data.events;
                renderEvents();
                updateButtonStates(data.has_more);
            })
            .catch(error => console.error('Error fetching events:', error));
    }

    // Завантаження унікальних значень для майстрів і систем
    function loadFilters() {
        fetch('/api/filters/')
            .then(response => response.json())
            .then(data => {
                populateFilter(elements.masterFilter, data.masters, 'Майстер');
                populateFilter(elements.systemFilter, data.systems, 'Система');
            })
            .catch(error => console.error('Error fetching filters:', error));
    }

    // Заповнення випадаючого списку унікальними значеннями з назвою поля як перше значення
    function populateFilter(selectElement, options, placeholder) {
        selectElement.innerHTML = `<option value="">${placeholder}</option>`;
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            selectElement.appendChild(opt);
        });
    }

    function parseEventDescription(summary, description) {
        // Регулярні вирази для витягування полів
        const summaryRegex = /^(.+?)(?:\s*[.-]\s*(?:Кімната\s.*\s)?)?[Мм]айстер\s(.+)$/;  // Витягуємо майстра та назву гри
        const freeSeatsRegex = /Вільні місця:\s(\d+)/;  // Витягуємо вільні місця
        const costRegex = /(?:[Вв]артість\s*:?\s*)(\d+(?:\s*[\wа-яА-Я]+)*)(?=\s*Щоб записатись|$)/;  // Витягуємо вартість
        const locationRegex = /(лісові|печерні|степові)\s*хухи/i;

        const gameMatch = summary.match(summaryRegex);
        const freeSeatsMatch = description.match(freeSeatsRegex);
        const costMatch = description.match(costRegex);
        const locationMatch = summary.match(locationRegex);

        // Парсинг результатів
        const master = gameMatch ? gameMatch[2] : '—';
        const game = gameMatch ? gameMatch[1].slice(0, 21) : 'Вільна кімната';
        const freeSeats = freeSeatsMatch ? parseInt(freeSeatsMatch[1], 10) : null;
        const cost = costMatch ? costMatch[1] : '—';
        const totalSeats = 5;
        const bookedSeatsText = freeSeats !== null ? `${totalSeats - freeSeats}/${totalSeats} місць заброньовані` : '—';

        // Determine location
        const location = locationMatch
            ? `${locationMatch[1][0].toUpperCase()}${locationMatch[1].slice(1).toLowerCase()} Хухи`
            : 'Онлайн партія';

        return {
            game,
            master,
            freeSeats,
            cost,
            bookedSeatsText,
            location,
            remainingDescription: description.split("Щоб записатись")[0].trim(),
        };
    }

    function renderEvents() {
        const carouselContainer = elements.calendarEvents;
        carouselContainer.innerHTML = '';

        const images = {
            'підземелля': "../static/images/calendar_pics/dd.png",
            'star': "../static/images/calendar_pics/sw.jpg",
            'вільна': "../static/images/calendar_pics/free_chamber.png",
            'coriolis': "../static/images/calendar_pics/coriolis_edit.jpg",
            'vampire': "../static/images/calendar_pics/vampire.jpg",
            'vessen': "../static/images/calendar_pics/vessen.jpg",
            'warhammer': "../static/images/calendar_pics/warhammer.jpg"
        };

        const defaultImage = "../static/images/calendar_pics/slay.png"; // Заглушка, якщо зображення немає

        allEvents.forEach(event => {
            const startDateTime = new Date(event.start);
            const endDateTime = new Date(event.end);

            // Формат дня, дати і часу
            const dayOfWeek = startDateTime.toLocaleDateString('uk-UA', { weekday: 'long' });
            const formattedDate = startDateTime.toLocaleDateString('uk-UA', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            const formattedTime = startDateTime.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
            const fullDateDisplay = `${dayOfWeek.charAt(0).toUpperCase() + dayOfWeek.slice(1)} | ${formattedDate} | ${formattedTime}`;

            const parsedDescription = parseEventDescription(event.summary, event.description || '');

            // Пошук відповідного зображення
            let gameImage = defaultImage;
            for (const key in images) {
                if (parsedDescription.game.toLowerCase().includes(key)) {
                    gameImage = images[key];
                    break;
                }
            }

            const eventImage = event.image_url || gameImage;

            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.innerHTML = `
                <img class="calendar-imgs" src="${gameImage}" alt="${parsedDescription.game}" class="event-image">
                <div class="event-card-content">
                    <h3><span>${event.summary}</span></h3>
                    <span class="game-name">${parsedDescription.game}</span>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/school.png">
                        <span class="span-for-icons">Майстер: ${parsedDescription.master}</span>
                    </div>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/calendar.png">
                        <span class="span-for-icons">${fullDateDisplay}</span>
                    </div>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/profit.png">
                        <span class="span-for-icons">${parsedDescription.cost}</span>
                    </div>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/group.png">
                        <span class="span-for-icons">${parsedDescription.bookedSeatsText}</span>
                    </div>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/location.png">
                        <span class="span-for-icons">${parsedDescription.location}</span>
                    </div>
                </div>
                <div class="telegram-button-container">
                    <a href="https://t.me/hyhu_space" class="sign-up" target="_blank">Записатись на гру</a>
                </div> 
            `;
            carouselContainer.appendChild(eventCard);
        });
    }

    function updateButtonStates(hasMore) {
        elements.prevBtn.disabled = currentPage === 1;
        elements.nextBtn.disabled = !hasMore;
    }

    // Додаємо обробники подій для фільтрів
    elements.datePicker.addEventListener('change', fetchEvents);
    elements.masterFilter.addEventListener('change', fetchEvents);
    elements.systemFilter.addEventListener('change', fetchEvents);

    elements.prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            fetchEvents();
        }
    });

    elements.nextBtn.addEventListener('click', () => {
        currentPage++;
        fetchEvents();
    });

    loadFilters();
    fetchEvents();
});
