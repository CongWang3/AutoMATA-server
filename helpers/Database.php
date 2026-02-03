<?php
class Database {
    private static $connection = null;
    
    public static function connect() {
        if (self::$connection === null) {
            $config = require __DIR__ . '/../config/database.php';
            self::$connection = mysqli_connect(
                '127.0.0.1',
                $config['username'],
                $config['password'],
                $config['database']
            );
            
            if (!self::$connection) {
                throw new Exception('Database connection failed: ' . mysqli_connect_error());
            }
        }
        return self::$connection;
    }
    
    public static function query($sql) {
        $con = self::connect();
        $result = mysqli_query($con, $sql);
        if (!$result) {
            throw new Exception('Query failed: ' . mysqli_error($con));
        }
        return $result;
    }
}