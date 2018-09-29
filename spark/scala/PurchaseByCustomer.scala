package com.sundogsoftware.spark

import org.apache.spark._
import org.apache.spark.SparkContext._
import org.apache.log4j._

object PurchaseByCustomer {
  
  def parseLine(line: String) = {
      val fields = line.split(",") //CustomerID, ItemID, AmountSpent
      
      val customerID = fields(0).toInt
      val amountSpent = fields(2).toFloat
      
      // Create a tuple that is our result.
      (customerID, amountSpent)
  }
  
  
    /** Our main function where the action happens */
  def main(args: Array[String]) {
   
    // Set the log level to only print errors
    Logger.getLogger("org").setLevel(Level.ERROR)
        
    // Create a SparkContext using every core of the local machine
    val sc = new SparkContext("local[*]", "PurchaseByCustomer")
  
    // Load each line of the source data into an RDD
    val lines = sc.textFile("../customer-orders.csv")
    
    // Use our parseLines function to convert to (customerID, amountSpent) tuples
    val rdd = lines.map(parseLine)
    
    // Lots going on here...
    // We are starting with an RDD of form (customerID, amountSpent) where customerID is the KEY and amountSpent is the VALUE
    // We use mapValues to convert each amountSpent value to a tuple of (amountSpent, 1)
    // Then we use reduceByKey to sum up the total amountSpent and total instances for each customerID, by
    // adding together all the amountSpent values and 1's respectively.
    val totalsByAge = rdd.mapValues(x => (x, 1)).reduceByKey( (x,y) => (x._1 + y._1, x._2 + y._2))
    
    // So now we have tuples of (age, (totalFriends, totalInstances))
    // To compute the average we divide totalFriends / totalInstances for each age.
    val outputNoCounter = totalsByAge.mapValues(x => x._1)
    
    // Collect the results from the RDD (This kicks off computing the DAG and actually executes the job)
    val results = outputNoCounter.collect()
    
    // Sort and print the final results.
    //results.sorted.foreach(println)

    //Flip and sort by amount spent
    
    val resultsSorted = results.map( x => (x._2, x._1) )
    
    resultsSorted.sorted.foreach(println)
    
  
  }
  
//adds up amount spent by each customer
// better solution in TotalSpentByCustomer.scala
  
}