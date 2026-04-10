/**
 * Module Materials Data
 * Maps each module to its PDF learning materials
 */

export interface PDFMaterial {
  id: string;
  title: string;
  filename: string;
  description: string;
}

export interface ModuleMaterials {
  moduleId: string;
  title: string;
  description: string;
  materials: PDFMaterial[];
}

export const moduleMaterialsData: Record<string, ModuleMaterials> = {
  CH01: {
    moduleId: 'CH01',
    title: 'CH01: Basic Selection & Filtering',
    description:
      'Learn the fundamentals of SQL data retrieval with SELECT statements, basic filtering with WHERE clauses, string operations, sorting with ORDER BY, and introductory set operations. This chapter covers the essential building blocks for querying relational databases effectively.',
    materials: [
      {
        id: 'ch01-basic-queries',
        title: 'SQL - Basic Queries',
        filename: 'SQL - Basic Queries.pdf',
        description: 'Introduction to SELECT, WHERE, and basic filtering operations',
      },
      {
        id: 'ch01-set-membership',
        title: 'SQL - Set Membership & WITH Clause',
        filename: 'SQL - Set Membership until With.pdf',
        description: 'Set operations, membership testing, and common table expressions',
      },
    ],
  },
  CH02: {
    moduleId: 'CH02',
    title: 'CH02: Aggregation & Grouping',
    description:
      'Master data aggregation using aggregate functions like COUNT, SUM, AVG, MIN, and MAX. Learn to group data with GROUP BY, filter aggregated results using HAVING, and apply conditional logic with CASE WHEN expressions. Includes nested subqueries for complex data analysis.',
    materials: [
      {
        id: 'ch02-set-membership',
        title: 'SQL - Set Membership & WITH Clause',
        filename: 'SQL - Set Membership until With.pdf',
        description: 'Advanced set operations and CTEs for complex queries',
      },
      {
        id: 'ch02-aggregate-functions',
        title: 'SQL - Aggregate Functions',
        filename: 'SQL - Aggregate Functions.pdf',
        description: 'Comprehensive guide to aggregate functions and grouping',
      },
    ],
  },
  CH03: {
    moduleId: 'CH03',
    title: 'CH03: Advanced Querying & Modification',
    description:
      'Explore advanced SQL concepts including explicit JOINs (INNER, OUTER, CROSS), Views and Materialized Views for query optimization, Data Manipulation (DML) and Data Definition (DDL) operations, Common Table Expressions (CTEs), and correlated subqueries for sophisticated data retrieval.',
    materials: [
      {
        id: 'ch03-aggregate-functions',
        title: 'SQL - Aggregate Functions',
        filename: 'SQL - Aggregate Functions.pdf',
        description: 'Advanced aggregation techniques and window functions',
      },
      {
        id: 'ch03-joins-views',
        title: 'SQL - Joins and Views',
        filename: 'SQL - Join and Views.pdf',
        description: 'Comprehensive coverage of JOIN operations and view management',
      },
    ],
  },
};

export const getModuleMaterials = (moduleId: string): ModuleMaterials | null => {
  return moduleMaterialsData[moduleId] || null;
};

export const getAllModuleMaterials = (): ModuleMaterials[] => {
  return Object.values(moduleMaterialsData);
};
