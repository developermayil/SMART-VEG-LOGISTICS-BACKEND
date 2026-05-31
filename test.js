const sql = require('mssql/msnodesqlv8');

const config = {
  connectionString: `
    Driver={ODBC Driver 17 for SQL Server};
    Server=localhost;
    Database=SmartVegLogistics;
    Trusted_Connection=Yes;
    TrustServerCertificate=Yes;
  `,
  
  driver: 'msnodesqlv8'
};

async function test() {
  try {
    await sql.connect(config);

    console.log('✅ Connected Successfully');

    const result = await sql.query(`
      SELECT 
        SYSTEM_USER AS CurrentUser,
        DB_NAME() AS DatabaseName
    `);

    console.log(result.recordset);

    await sql.close();

  } catch (err) {

    console.log('❌ Error');
    console.log(err);

  }
}

test();