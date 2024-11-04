document.addEventListener('DOMContentLoaded', () => {
    const selectors = {
        calendarEvents: 'calendar-events',
        eventsUrl: 'events-url',
        prevBtn: 'prev-btn',
        nextBtn: 'next-btn',
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
        fetch(`${elements.eventsUrl.dataset.url}?page=${currentPage}&limit=${eventsPerPage}`)
            .then(response => response.json())
            .then(data => {
                allEvents = data.events;
                renderEvents();
                updateButtonStates(data.has_more);
            })
            .catch(error => console.error('Error fetching events:', error));
    }

    function parseEventDescription(summary, description) {
        // Регулярні вирази для витягування полів
        const summaryRegex = /^(.+?)(?:\s*[.-]\s*(?:Кімната\s.*\s)?)?[Мм]айстер\s(.+)$/;  // Витягуємо майстра та назву гри
        const freeSeatsRegex = /Вільні місця:\s(\d+)/;  // Витягуємо вільні місця
        const costRegex = /(?:[Вв]артість\s*:?\s*)(\d+(?:\s*[\wа-яА-Я]+)*)(?=\s*Щоб записатись|$)/;  // Витягуємо вартість
        // /(?:[Вв]артість\s*:?\s*)(\d+(?:\s*[\wа-яА-Я]+)*)/;
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
            ? `${locationMatch[1][0].toUpperCase()}${locationMatch[1].slice(1).toLowerCase()} Хухи`  // Corrected capitalization and structure
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
            'підземелля': "../static/images/dd.png",
            'star': "../static/images/sw.jpg",
            'вільна': "../static/images/free_chamber.png",
            'coriolis': "../static/images/coriolis_edit.jpg",
            'vampire': "../static/images/vampire.jpg",
            'vessen': "../static/images/vessen.jpg",
            'warhammer': "../static/images/warhammer.jpg"
        };

        const defaultImage = "../static/images/slay.png"; // Заглушка, якщо зображення немає

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


            // console.log('Game Name:', parsedDescription.game); // Debugging
            // console.log('Image Path:', gameImage);
            const eventImage = event.image_url || gameImage; // Використовуємо зображення з події або локальне

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
                    
                    <!-- <p>${parsedDescription.remainingDescription}</p> -->
                    
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

    fetchEvents();
});
