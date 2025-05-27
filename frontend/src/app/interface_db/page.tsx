"use client";

import { useState, useEffect, useCallback } from 'react';
import { DataQuillLayout } from '@/components/dataquill/DataQuillLayout';
import { SchemaBrowser, type SchemaData } from '@/components/dataquill/SchemaBrowser';
import { SqlEditor } from '@/components/dataquill/SqlEditor';
import { ResultsTable } from '@/components/dataquill/ResultsTable';
import { useToast } from "@/hooks/use-toast";



const DUMMY_SCHEMA_DATA: SchemaData = [
  {
    id: 'db_sales',
    name: 'SalesDB',
    type: 'database',
    children: [
      {
        id: 'tbl_customers',
        name: 'Customers',
        type: 'table',
        children: [
          {
            id: 'fld_cols_customers',
            name: 'Columns',
            type: 'folder',
            children: [
              { id: 'col_cust_id', name: 'CustomerID', type: 'column', dataType: 'INT', isPK: true },
              { id: 'col_cust_name', name: 'CustomerName', type: 'column', dataType: 'VARCHAR(255)' },
              { id: 'col_contact_name', name: 'ContactName', type: 'column', dataType: 'VARCHAR(255)' },
              { id: 'col_country', name: 'Country', type: 'column', dataType: 'VARCHAR(100)' },
            ],
          },
          {
            id: 'fld_idx_customers',
            name: 'Indexes',
            type: 'folder',
            children: [
              { id: 'idx_pk_customers', name: 'PK_Customers', type: 'index', indexType: 'PRIMARY' },
              { id: 'idx_country_customers', name: 'IX_Country_Customers', type: 'index', indexType: 'INDEX' },
            ],
          },
        ],
      },
      {
        id: 'tbl_orders',
        name: 'Orders',
        type: 'table',
        children: [
          {
            id: 'fld_cols_orders',
            name: 'Columns',
            type: 'folder',
            children: [
              { id: 'col_order_id', name: 'OrderID', type: 'column', dataType: 'INT', isPK: true },
              { id: 'col_order_cust_id', name: 'CustomerID', type: 'column', dataType: 'INT', isFK: true },
              { id: 'col_order_date', name: 'OrderDate', type: 'column', dataType: 'DATE' },
            ],
          },
          {
            id: 'fld_idx_orders',
            name: 'Indexes',
            type: 'folder',
            children: [
              { id: 'idx_pk_orders', name: 'PK_Orders', type: 'index', indexType: 'PRIMARY' },
              { id: 'idx_fk_customer_orders', name: 'IX_CustomerID_Orders', type: 'index', indexType: 'INDEX' },
            ],
          },
        ],
      },
    ],
  },
  {
    id: 'db_inventory',
    name: 'InventoryDB',
    type: 'database',
    children: [
      {
        id: 'tbl_products',
        name: 'Products',
        type: 'table',
        children: [
          {
            id: 'fld_cols_products',
            name: 'Columns',
            type: 'folder',
            children: [
              { id: 'col_prod_id', name: 'ProductID', type: 'column', dataType: 'INT', isPK: true },
              { id: 'col_prod_name', name: 'ProductName', type: 'column', dataType: 'VARCHAR(255)' },
            ],
          },
          {
            id: 'fld_idx_products',
            name: 'Indexes',
            type: 'folder',
            children: [
              { id: 'idx_pk_products', name: 'PK_Products', type: 'index', indexType: 'PRIMARY' },
            ],
          },
        ],
      },
    ],
  },
];

interface QueryResult {
  columns: { key: string; name: string }[];
  rows: { [key: string]: any }[];
}

export default function DataQuillPage() {
  const [sqlQuery, setSqlQuery] = useState<string>('SELECT * FROM Customers WHERE Country = \'Germany\';');
  const [schema, setSchema] = useState<SchemaData>(DUMMY_SCHEMA_DATA);
  const [results, setResults] = useState<QueryResult>({ columns: [], rows: [] });
  const [queryError, setQueryError] = useState<string | null>(null);
  const [isLoadingQuery, setIsLoadingQuery] = useState<boolean>(false);
  const [executionTime, setExecutionTime] = useState<number | undefined>(undefined);
  const [rowCount, setRowCount] = useState<number | undefined>(undefined);

  const { toast } = useToast();

  const handleRunQuery = useCallback(async () => {
    setIsLoadingQuery(true);
    setQueryError(null);
    setResults({ columns: [], rows: [] });
    setExecutionTime(undefined);
    setRowCount(undefined);

    const startTime = performance.now();

    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));

    const endTime = performance.now();
    const timeTaken = endTime - startTime;
    setExecutionTime(timeTaken);

    const lowerQuery = sqlQuery.trim().toLowerCase();

    if (lowerQuery.startsWith('select * from customers')) {
      const newResults: QueryResult = {
        columns: [
          { key: 'CustomerID', name: 'CustomerID' },
          { key: 'CustomerName', name: 'CustomerName' },
          { key: 'ContactName', name: 'ContactName' },
          { key: 'Country', name: 'Country' },
        ],
        rows: [
          { CustomerID: 1, CustomerName: 'Alfreds Futterkiste', ContactName: 'Maria Anders', Country: 'Germany' },
          { CustomerID: 2, CustomerName: 'Ana Trujillo Emparedados y helados', ContactName: 'Ana Trujillo', Country: 'Mexico' },
          { CustomerID: 3, CustomerName: 'Antonio Moreno Taquería', ContactName: 'Antonio Moreno', Country: 'Mexico' },
        ]
        // .filter(row => lowerQuery.includes("germany") ? row.Country === 'Germany' : true),
      };
      setResults(newResults);
      setRowCount(newResults.rows.length);
    } else if (lowerQuery.startsWith('select * from products')) {
      const newResults: QueryResult = {
        columns: [
          { key: 'ProductID', name: 'ProductID' },
          { key: 'ProductName', name: 'ProductName' },
        ],
        rows: [
          { ProductID: 1, ProductName: 'Chai' },
          { ProductID: 2, ProductName: 'Chang' },
        ],
      };
      setResults(newResults);
      setRowCount(newResults.rows.length);
    } else if (lowerQuery.startsWith('create table') || lowerQuery.startsWith('alter table') || lowerQuery.startsWith('drop table')) {
      setResults({ columns: [], rows: [] });
      setRowCount(0);
      toast({
        title: "DDL Executed",
        description: "Schema modification query executed successfully.",
        variant: "default",
      });
    } else if (lowerQuery.includes('error_test')) {
      setQueryError('Simulated SQL Error: Syntax error near "error_test". Please check your query.');
    } else {
      setResults({ columns: [], rows: [] });
      setQueryError('No results for this query or query not recognized by dummy handler. Try "SELECT * FROM Customers" or "SELECT * FROM Products".');
    }

    setIsLoadingQuery(false);
  }, [sqlQuery, toast]);

  const handleRefreshSchema = useCallback(async () => {
    toast({
      title: "Schema Refresh",
      description: "Simulating schema refresh...",
    });

    await new Promise(resolve => setTimeout(resolve, 1500));

    setSchema([...DUMMY_SCHEMA_DATA]);

    toast({
      title: "Schema Refreshed",
      description: "Schema has been updated.",
      variant: "default",
    });
  }, [toast]);

  return (
    <DataQuillLayout
      schemaBrowser={<SchemaBrowser schema={schema} />}
      handleRefreshSchema={handleRefreshSchema}
      onRunQuery={handleRunQuery}
      sqlEditor={
        <SqlEditor
          query={sqlQuery}
          onQueryChange={setSqlQuery}
          
        />
      }
      resultsTable={
        <ResultsTable
          columns={results.columns}
          rows={results.rows}
          error={queryError}
          isLoading={isLoadingQuery}
          executionTime={executionTime}
          rowCount={rowCount}
        />
      }
    />
  );
}
