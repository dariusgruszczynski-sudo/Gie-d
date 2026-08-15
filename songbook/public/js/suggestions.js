// suggestions.js — gotowe propozycje piosenek do dodania jednym kliknięciem.
// To metadane (tytuł, wykonawca, tonacja, tempo, tagi) — bez tekstu i chwytów
// (te pobierzesz modułem „Wyszukaj"). Dobrane pod gitarę/ognisko/standardy.

export const SUGGEST_PL = [
  { title: 'Whisky', artist: 'Dżem', key: 'a', tempo: 72, tags: ['blues', 'polski', 'ognisko'] },
  { title: 'Autobiografia', artist: 'Perfect', key: 'e', tempo: 132, tags: ['rock', 'polski', 'klasyk'] },
  { title: 'Takie tango', artist: 'Budka Suflera', key: 'a', tempo: 120, tags: ['rock', 'polski'] },
  { title: 'Kocham cię kochanie moje', artist: 'Maanam', key: 'C', tempo: 116, tags: ['rock', 'polski'] },
  { title: 'Zamki na piasku', artist: 'Lady Pank', key: 'e', tempo: 138, tags: ['rock', 'polski'] },
  { title: 'Arahja', artist: 'Kult', key: 'a', tempo: 92, tags: ['rock', 'polski'] },
  { title: 'Moja i twoja nadzieja', artist: 'Hey', key: 'D', tempo: 120, tags: ['rock', 'polski'] },
  { title: 'Baśka', artist: 'Wilki', key: 'G', tempo: 128, tags: ['pop-rock', 'polski', 'impreza'] },
  { title: 'Warszawa', artist: 'T.Love', key: 'C', tempo: 124, tags: ['rock', 'polski'] },
  { title: 'Czarny blues o czwartej nad ranem', artist: 'Stare Dobre Małżeństwo', key: 'a', tempo: 96, tags: ['poezja śpiewana', 'ognisko'] },
  { title: 'Nie spoczniemy', artist: 'Czerwone Gitary', key: 'a', tempo: 120, tags: ['klasyk', 'polski'] },
  { title: 'Długość dźwięku samotności', artist: 'Myslovitz', key: 'h', tempo: 120, tags: ['rock', 'polski'] },
  { title: 'Jestem z miasta', artist: 'Elektryczne Gitary', key: 'C', tempo: 132, tags: ['rock', 'polski', 'impreza'] },
  { title: 'Kołysanka dla nieznajomej', artist: 'Perfect', key: 'e', tempo: 96, tags: ['rock', 'polski'] },
  { title: 'Hej Sokoły', artist: 'trad.', key: 'a', tempo: 132, tags: ['ognisko', 'ludowa'] },
];

export const SUGGEST_WORLD = [
  { title: 'Let It Be', artist: 'The Beatles', key: 'C', tempo: 72, tags: ['klasyk', 'ognisko'] },
  { title: "Knockin' on Heaven's Door", artist: 'Bob Dylan', key: 'G', tempo: 68, tags: ['klasyk', 'ognisko'] },
  { title: 'Hotel California', artist: 'Eagles', key: 'a', tempo: 74, tags: ['rock', 'klasyk'] },
  { title: 'Wonderwall', artist: 'Oasis', key: 'F#m', capo: 2, tempo: 87, tags: ['rock', 'ognisko'] },
  { title: 'Come As You Are', artist: 'Nirvana', key: 'e', tempo: 120, tags: ['grunge', 'rock'] },
  { title: 'Perfect', artist: 'Ed Sheeran', key: 'G', capo: 1, tempo: 63, tags: ['pop', 'ballada'] },
  { title: 'Take Me Home, Country Roads', artist: 'John Denver', key: 'A', tempo: 82, tags: ['folk', 'ognisko'] },
  { title: "Sweet Child o' Mine", artist: "Guns N' Roses", key: 'D', tempo: 122, tags: ['rock', 'klasyk'] },
  { title: 'Nothing Else Matters', artist: 'Metallica', key: 'e', tempo: 92, tags: ['rock', 'ballada'] },
  { title: 'Yellow', artist: 'Coldplay', key: 'G', capo: 0, tempo: 87, tags: ['pop-rock', 'ognisko'] },
  { title: 'Let Her Go', artist: 'Passenger', key: 'G', capo: 7, tempo: 75, tags: ['folk', 'pop'] },
  { title: 'House of the Rising Sun', artist: 'The Animals', key: 'a', tempo: 76, tags: ['klasyk', 'ognisko'] },
  { title: 'Hallelujah', artist: 'Leonard Cohen', key: 'C', tempo: 60, tags: ['ballada', 'ognisko'] },
  { title: 'Losing My Religion', artist: 'R.E.M.', key: 'a', tempo: 125, tags: ['rock', 'klasyk'] },
  { title: 'Californication', artist: 'Red Hot Chili Peppers', key: 'a', tempo: 96, tags: ['rock'] },
];
