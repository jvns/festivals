const app = Vue.createApp({
  async mounted() {
    this.readHash();
    window.addEventListener(
      "hashchange",
      () => {
        console.log("hashchange");
        this.readHash();
      },
      false,
    );
    // get language from local storage if possible
    const language = localStorage.getItem("language");
    if (language) {
      this.language = language;
    }
    const json = await fetch("performances-2025.json");
    const performances = await json.json();
    // map title to performance
    for (const performance of performances) {
      if (performance.performances.dates.length == 0) {
        continue;
      }
      this.performances[performance.title] = performance;
    }
  },
  data() {
    return {
      performances: {},
      titles: [],
      hoveredShow: undefined,
      language: "en",
    };
  },
  // put titles in hash when they change
  watch: {
    titles() {
      const hash = this.titles.join("::");
      window.location.hash = hash;
    },
    language() {
      localStorage.setItem("language", this.language);
    },
  },
  computed: {
    english() {
      return this.language === "en";
    },
    minIntervals() {
      const intervals = {};
      for (const day of this.fringeDates()) {
        const shows = this.fringeShows(day);
        if (shows.length === 0) {
          intervals[day] = 0;
        } else {
          intervals[day] = Math.min(...shows.map(show => show.interval));
        }
      }
      return intervals;
    },
  },
  methods: {
    readHash() {
      const hash = decodeURIComponent(window.location.hash.slice(1));
      if (hash) {
        this.titles = hash.split("::");
      } else {
        this.titles = [];
      }
    },
    performanceTitles() {
      const titles = Object.keys(this.performances);
      //sort, ignore case
      titles.sort((a, b) =>
        a.localeCompare(b, undefined, { sensitivity: "base" }),
      );
      return titles;
    },
    testMethod() {
      return "hello!";
    },
    formatDate(date, lang) {
      // translate 07/06/2025 to 'June 7'
      const [day, month, _year] = date.split("/");
      if (month == 6) {
          if (lang === "en") {
            return `June ${parseInt(day)}`;
          }
          return `${parseInt(day)} juin`;
      } else if (month == 5) {
          if (lang === "en") {
            return `May ${parseInt(day)}`;
          }
          return `${parseInt(day)} mai`;
      }
    },
    fringeShows(day) {
      const shows = [];
      for (const title of this.titles) {
        const performance = this.performances[title];
        if (performance && performance.performances.times[day]) {
          const time = performance.performances.times[day][0].performanceTime;
          const [hour, minute] = time.split(":").map(Number);
          const interval = hour * 4 + Math.floor(minute / 15);
          shows.push({
              title: performance.title,
              link: performance.link,
              time: performance.performances.times[day][0].performanceTime,
              interval: interval,
              duration: Math.ceil(performance.duration.split(" ")[0] / 15),
          })
        }
      }
      // sort shows by time
      shows.sort((a, b) => {
        return a.time < b.time ? -1 : 1;
      });
      return shows;
    },
    fringeDates() {
      return [
        "26/05/2025",
        "27/05/2025",
        "28/05/2025",
        "29/05/2025",
        "30/05/2025",
        "31/05/2025",
        "01/06/2025",
        "02/06/2025",
        "03/06/2025",
        "04/06/2025",
        "05/06/2025",
        "06/06/2025",
        "07/06/2025",
        "08/06/2025",
        "09/06/2025",
        "10/06/2025",
        "11/06/2025",
        "12/06/2025",
        "13/06/2025",
        "14/06/2025",
        "15/06/2025",
      ];
    },
  },
});
app.component("vue-multiselect", window["vue-multiselect"].default);
app.mount("#app");
