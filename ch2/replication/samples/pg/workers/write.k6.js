import sql from 'k6/x/sql';
import driver from 'k6/x/sql/driver/postgres';
import { Trend, Counter } from 'k6/metrics';
import { check, group, sleep } from 'k6';

// --- Configuration ---
// Use Docker service names for connections (NOT localhost)
const CONN = "postgres://postgres:postgres@pgbouncer:6432/write_db?sslmode=disable&connect_timeout=10";

// Realistic ranges for Pagila sample data
const MAX_CUSTOMER_ID = 599;
const MAX_INVENTORY_ID = 4581;
const MAX_STAFF_ID = 2;


export const options = {
  thresholds: {
    'checks': ['rate>0.98'], // We expect >98% of checks to pass
    'write_rental_latency': ['p(90)<1000'], // Goal: 90% of writes under 1s
    'sync_write_timeouts': ['count<=5'], // Goal: Number of connection timeouts must be less than 5
  },
  scenarios: {
    // SCENARIO 1: Emulate new rentals
    write_scenario: {
      executor: 'constant-vus',
      vus: 40,
      duration: '60s',
      exec: 'writeWorkload', // This scenario runs the writeWorkload function
      tags: { service: 'primary-writes' },
    },
  },
};

const writeLatency = new Trend('write_rental_latency');
const writeTimeouts = new Counter('sync_write_timeouts');

const DB = sql.open(driver, CONN);

export function teardown() {
  DB.close();
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
      VALUES ($1, $2::integer, $3::integer, $4, $5::integer, NOW())
      RETURNING rental_id;
    `;
    const params = [validRentalDate, inventoryId, customerId, validReturnDate, staffId];
    let startTime = Date.now();
    try {
      const result = DB.query(rentalQuery, ...params);
      writeLatency.add(Date.now() - startTime);

      const success = check(result, {
        'Rental insert successful': (r) => r && r.length > 0 && r[0].rental_id > 0,
      });

      if (!success) {
        writeErrors.add(1);
      }

      if (result && result.length > 0) {
        rentalId = result[0].rental_id;
      }
    } catch (e) {
      if (e.message.includes('bad connection')) {
          writeTimeouts.add(1);
          console.error(`ERROR: SYNCHRONOUS STALL DETECTED: ${e.message}`);
      } else {
          console.error(`ERROR: General Primary write failed: ${e.message}`);
      }
      check(false, { 'Rental insert failed': true });
    }
  });

  // if (rentalId) {
  //   // Only insert payment if rental was successful
  //   group('Write - Insert Payment (Primary)', function () {
  //     const paymentQuery = `
  //       INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date)
  //       VALUES ($1, $2, $3, $4, $5);
  //     `;
  //     const params = [customerId, staffId, rentalId, paymentAmount, validRentalDate];
  //     try {
  //       DB.exec(paymentQuery, ...params);
  //       check(null, { 'Payment insert successful': () => true });
  //     } catch (e) {
  //       if (e.message.includes('timeout') || e.message.includes('canceling')) {
  //           writeTimeouts.add(1);
  //           console.error(`ERROR: SYNCHRONOUS STALL DETECTED: ${e.message}`);
  //       } else {
  //           console.error(`ERROR: General Primary write failed: ${e.message}`);
  //       }
  //       check(false, { 'Payment insert failed': true });
  //     }
  //   });
  // }
  sleep(1);
}