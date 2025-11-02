import sql from 'k6/x/sql';
import driver from 'k6/x/sql/driver/postgres';
import { Trend } from 'k6/metrics';
import { check, group, sleep } from 'k6';

// --- Configuration ---
// Use Docker service names for connections (NOT localhost)
const CONN = "postgres://postgres:postgres@pgbouncer:5432/read_db?sslmode=disable";

const MAX_FILM_ID = 1000; // Pagila has 1000 films

// --- k6 Options ---
export const options = {
  thresholds: {
    'checks': ['rate>0.98'], // We expect >98% of checks to pass
    'read_film_latency': ['p(90)<500'],  // Goal: 90% of reads under 500ms
  },
  scenarios: {
    // SCENARIO 2: Emulate new updates
    read_scenario: {
      executor: 'constant-vus',
      vus: 100,
      duration: '60s',
      exec: 'readWorkload', // This scenario runs the readWorkload function
      tags: { service: 'standby-reads' },
    },
  },
};

const readLatency = new Trend('read_film_latency');
const DB = sql.open(driver, CONN);

export function teardown() {
  DB.close();
}

export function readWorkload() {
  // Simulate a user browsing for a film
  const filmId = Math.floor(Math.random() * MAX_FILM_ID) + 1;

  group('Read - Get Film Details (Standby)', function () {
    const filmQuery = `
      SELECT f.title, f.description, f.release_year, l.name AS language
      FROM film f
      JOIN language l ON f.language_id = l.language_id
      WHERE f.film_id = $1;
    `;
    let startTime = Date.now();
    try {
      const result = standbyDB.query(filmQuery, filmId);
      readLatency.add(Date.now() - startTime); // Custom metric

      check(result, {
        'Film query successful': (r) => r && r.length > 0,
      });
    } catch (e) {
      console.error(`Error on film read: ${e}`);
      check(false, { 'Film query failed': true });
    }
  });

  sleep(0.5); // Shorter think time for browsing
}