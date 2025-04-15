import { Project, SyntaxKind, Node, ClassDeclaration } from "ts-morph";
import fs from "fs";

type Metric = {
  className: string;
  filePath: string;
  loc: number;
  cbo: number;
  wmc: number;
  dit: number;
  rfc: number;
  lcom: number;
  totalMethods: number;
  totalFields: number;
  nosi: number;
  returnQty: number;
  loopQty: number;
  comparisonsQty: number;
  tryCatchQty: number;
  parenthesizedExpsQty: number;
  stringLiteralsQty: number;
  numbersQty: number;
  assignmentsQty: number;
  mathOperationsQty: number;
  variablesQty: number;
  maxNestedBlocks: number;
  uniqueWordsQty: number;
};

const metrics: Metric[] = [];

function countNodeKind(node: Node, kind: SyntaxKind): number {
  return node.getDescendantsOfKind(kind).length;
}
function countVariables(cls: ClassDeclaration): number {
  const fields = cls.getProperties(); // Variáveis de instância (propriedades)
  // const methods = cls.getMethods();  // Variáveis locais e parâmetros

  let totalVariables = fields.length;

  // methods.forEach((method) => {
  //   const localVars = method.getDescendantsOfKind(SyntaxKind.Identifier)
  //     .filter(identifier => identifier.getParent()?.getKind() !== SyntaxKind.Parameter);
  //   totalVariables += localVars.length;
  // });

  return totalVariables;
}

function countUniqueWords(text: string): number {
  const words = text.match(/\b\w+\b/g);
  return words ? new Set(words).size : 0;
}

const project = new Project({
  skipAddingFilesFromTsConfig: true,
});


function getMaxNestedDepth(node: Node, currentDepth = 0): number {
  if (node.getKind() === SyntaxKind.Block) {
    currentDepth += 1;
  }

  let maxDepth = currentDepth;

  node.forEachChild((child) => {
    const childDepth = getMaxNestedDepth(child, currentDepth);
    if (childDepth > maxDepth) {
      maxDepth = childDepth;
    }
  });

  return maxDepth;
}



function calculateDIT(cls: ClassDeclaration): number {
  let level = 0;
  let current = cls;

  while (true) {
    const baseClass = current.getExtends();
    if (!baseClass) break;

    const baseName = baseClass.getExpression().getText();
    const baseDeclaration = project.getSourceFiles().flatMap(f => f.getClasses()).find(c => c.getName() === baseName);
    
    if (!baseDeclaration) break;

    level++;
    current = baseDeclaration;
  }

  return level;
}



function getCyclomaticComplexity(method: Node): number {
  let complexity = 1; // todo método começa com complexidade 1

  const controlFlowKinds = [
    SyntaxKind.IfStatement,
    SyntaxKind.ForStatement,
    SyntaxKind.ForOfStatement,
    SyntaxKind.ForInStatement,
    SyntaxKind.WhileStatement,
    SyntaxKind.CaseClause,
    SyntaxKind.CatchClause,
    SyntaxKind.ConditionalExpression, // operador ternário
    SyntaxKind.BinaryExpression // pode conter && ou ||
  ];

  method.forEachDescendant((descendant) => {
    const kind = descendant.getKind();

    if (controlFlowKinds.includes(kind)) {
      complexity++;
    }

    // contar operadores lógicos que influenciam caminhos
    if (kind === SyntaxKind.BinaryExpression) {
      const op = descendant.asKind(SyntaxKind.BinaryExpression)?.getOperatorToken().getKind();
      if (op === SyntaxKind.AmpersandAmpersandToken || op === SyntaxKind.BarBarToken) {
        complexity++;
      }
    }
  });

  return complexity;
}

function calculateLCOM(cls: ClassDeclaration): number {
  const methods = cls.getMethods();
  const fields = cls.getProperties().map(p => p.getName());

  let nonSharedPairs = 0;
  let sharedPairs = 0;

  for (let i = 0; i < methods.length; i++) {
    for (let j = i + 1; j < methods.length; j++) {
      const methodA = methods[i];
      const methodB = methods[j];

      const accessedByA = new Set(
        methodA.getDescendantsOfKind(SyntaxKind.Identifier)
          .map(id => id.getText())
          .filter(name => fields.includes(name))
      );

      const accessedByB = new Set(
        methodB.getDescendantsOfKind(SyntaxKind.Identifier)
          .map(id => id.getText())
          .filter(name => fields.includes(name))
      );

      const shared = [...accessedByA].some(name => accessedByB.has(name));

      if (shared) {
        sharedPairs++;
      } else {
        nonSharedPairs++;
      }
    }
  }

  return Math.max(nonSharedPairs - sharedPairs, 0);
}


project.addSourceFilesAtPaths("src/**/*.ts");

project.getSourceFiles().forEach((sourceFile) => {
  const fileText = sourceFile.getFullText();
  const loc = fileText.split("\n").length;
  const filePath = sourceFile.getFilePath();

  sourceFile.getClasses().forEach((cls) => {
    const className = cls.getName() || "Unnamed";
    const parentClass = cls.getExtends()?.getText();
    const methods = cls.getMethods();
    const properties = cls.getProperties();

    const calledMethods = new Set<string>();
    cls.getDescendantsOfKind(SyntaxKind.CallExpression).forEach((call) => {
      const exp = call.getExpression();
      if (exp.getKind() === SyntaxKind.Identifier) {
        calledMethods.add(exp.getText());
      }
    });

    const cbo = new Set<string>();
    cls.getDescendantsOfKind(SyntaxKind.Identifier).forEach((id) => {
      const name = id.getText();
      if (name !== className) cbo.add(name);
    });
    const explicitProperties = cls.getProperties();
    const constructorProperties = cls.getConstructors().flatMap((ctor) =>
      ctor.getParameters().filter((param) => param.getScope() !== undefined)
    );

    const totalFields = explicitProperties.length + constructorProperties.length;
    const maxNested = getMaxNestedDepth(cls) - 1;
    let wmc = 0;
    methods.forEach((method) => {
      wmc += getCyclomaticComplexity(method);
    });

    metrics.push({
      className,
      filePath,
      loc,
      cbo: cbo.size,
      wmc: wmc,
      dit: calculateDIT(cls),
      rfc: calledMethods.size + methods.length,
      lcom: calculateLCOM(cls),
      totalMethods: methods.length,
      totalFields: properties.length + totalFields,
      nosi: 0,
      returnQty: countNodeKind(cls, SyntaxKind.ReturnStatement),
      loopQty:
        countNodeKind(cls, SyntaxKind.ForStatement) +
        countNodeKind(cls, SyntaxKind.ForOfStatement) +
        countNodeKind(cls, SyntaxKind.WhileStatement),
      comparisonsQty:
        countNodeKind(cls, SyntaxKind.EqualsEqualsToken) +
        countNodeKind(cls, SyntaxKind.EqualsEqualsEqualsToken) +
        countNodeKind(cls, SyntaxKind.ExclamationEqualsEqualsToken) +
        countNodeKind(cls, SyntaxKind.ExclamationEqualsToken),
      tryCatchQty: countNodeKind(cls, SyntaxKind.TryStatement),
      parenthesizedExpsQty: countNodeKind(cls, SyntaxKind.ParenthesizedExpression),
      stringLiteralsQty: countNodeKind(cls, SyntaxKind.StringLiteral),
      numbersQty: countNodeKind(cls, SyntaxKind.NumericLiteral),
      assignmentsQty: countNodeKind(cls, SyntaxKind.EqualsToken),
      mathOperationsQty:
        countNodeKind(cls, SyntaxKind.PlusToken) +
        countNodeKind(cls, SyntaxKind.MinusToken) +
        countNodeKind(cls, SyntaxKind.AsteriskToken) +
        countNodeKind(cls, SyntaxKind.SlashToken),
      variablesQty: countVariables(cls),
      maxNestedBlocks: maxNested,
      uniqueWordsQty: countUniqueWords(cls.getText()),
    });
  });
});

// Atualizar NOSI (Number of Subclasses Inheriting)
metrics.forEach((cls) => {
  const subclasses = project.getSourceFiles().flatMap(f => f.getClasses()).filter(sub => {
    const base = sub.getExtends()?.getExpression().getText();
    return base === cls.className;
  });

  cls.nosi = subclasses.length;
});

fs.writeFileSync("class_metrics.json", JSON.stringify(metrics, null, 2));
console.log("✅ Métricas detalhadas exportadas para class_metrics.json");