import sql from 'k6/x/sql';
import driver from 'k6/x/sql/driver/postgres';
import { Trend } from 'k6/metrics';
import { check, group, sleep } from 'k6';

// --- Configuration ---
// Use Docker service names for connections (NOT localhost)
const PRIMARY_CONN = "postgres://postgres:postgres@postgres-primary:5432/db?sslmode=disable";
const STANDBY_CONN = "postgres://postgres:postgres@postgres-standby:5432/db?sslmode=disable";

// Realistic ranges for Pagila sample data
const MAX_CUSTOMER_ID = 599;
const MAX_INVENTORY_ID = 4581;
const MAX_STAFF_ID = 2;
const MAX_FILM_ID = 1000; // Pagila has 1000 films

// --- k6 Options ---
export const options = {
  thresholds: {
    'checks': ['rate>0.98'], // We expect >98% of checks to pass
    'write_rental_latency': ['p(90)<1000'], // Goal: 90% of writes under 1s
    'read_film_latency': ['p(90)<500'],  // Goal: 90% of reads under 500ms
  },
  scenarios: {
    // SCENARIO 1: Emulate new rentals
    write_scenario: {
      executor: 'constant-vus',
      vus: 20,
      duration: '300s',
      exec: 'writeWorkload', // This scenario runs the writeWorkload function
      tags: { service: 'primary-writes' },
    },
    // SCENARIO 2: Emulate new updates
    read_scenario: {
      executor: 'constant-vus',
      vus: 30,
      duration: '300s',
      exec: 'readWorkload', // This scenario runs the readWorkload function
      tags: { service: 'standby-reads' },
    },
  },
};

const writeLatency = new Trend('write_rental_latency');
const readLatency = new Trend('read_film_latency');

const primaryDB = sql.open(driver, PRIMARY_CONN);
const standbyDB = sql.open(driver, STANDBY_CONN);

export function teardown() {
  primaryDB.close();
  standbyDB.close();
}

export function writeWorkload() {
  // Generate random data for a new rental and its payment
  const customerId = Math.floor(Math.random() * MAX_CUSTOMER_ID) + 1;
  const inventoryId = Math.floor(Math.random() * MAX_INVENTORY_ID) + 1;
  const staffId = Math.floor(Math.random() * MAX_STAFF_ID) + 1;
  const paymentAmount = (Math.random() * 10 + 1).toFixed(2);

  // Use a date from the Pagila dataset's range. To follow the current partition schema
  const validRentalDate = '2022-02-15T10:30:00Z';
  const validReturnDate = '2022-03-22T10:30:00Z';
  
  let rentalId = null;

  group('Write - Insert Rental (Primary)', function () {
    const rentalQuery = `
      INSERT INTO rental (rental_date, inventory_id, customer_id, return_date, staff_id, last_update)
      VALUES ($1, $2, $3, $4, $5, NOW())
      RETURNING rental_id;
    `;
    const params = [validRentalDate, inventoryId, customerId, validReturnDate, staffId];
    let startTime = Date.now();
    try {
      const result = primaryDB.query(rentalQuery, ...params);
      writeLatency.add(Date.now() - startTime);

      check(result, {
        'Rental insert successful': (r) => r && r.length > 0 && r[0].rental_id > 0,
      });
      if (result && result.length > 0) {
        rentalId = result[0].rental_id;
      }
    } catch (e) {
      console.error(`Error on rental insert: ${e}`);
      check(false, { 'Rental insert failed': true });
    }
  });

  if (rentalId) {
    // Only insert payment if rental was successful
    group('Write - Insert Payment (Primary)', function () {
      const paymentQuery = `
        INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date)
        VALUES ($1, $2, $3, $4, $5);
      `;
      const params = [customerId, staffId, rentalId, paymentAmount, validRentalDate];
      try {
        primaryDB.exec(paymentQuery, ...params);
        check(null, { 'Payment insert successful': () => true });
      } catch (e) {
        console.error(`Error on payment insert: ${e}`);
        check(false, { 'Payment insert failed': true });
      }
    });
  }
  sleep(1);
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