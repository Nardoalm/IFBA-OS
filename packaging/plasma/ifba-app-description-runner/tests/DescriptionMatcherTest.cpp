/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "../descriptionmatcher.h"

#include <QObject>
#include <QtTest>

class DescriptionMatcherTest : public QObject
{
    Q_OBJECT

private Q_SLOTS:
    void findsDescriptionCaseInsensitively()
    {
        QVERIFY(IfbaAppSearch::matchesDescription(
            QStringLiteral("Browse the web and manage bookmarks"), QStringLiteral("WEB")));
    }

    void requiresEverySearchTermInTheDescription()
    {
        QVERIFY(IfbaAppSearch::matchesDescription(
            QStringLiteral("Browse the web and manage bookmarks"), QStringLiteral("web bookmarks")));
        QVERIFY(!IfbaAppSearch::matchesDescription(
            QStringLiteral("Browse the web and manage bookmarks"), QStringLiteral("web calculator")));
    }

    void rejectsEmptyInput()
    {
        QVERIFY(!IfbaAppSearch::matchesDescription(QString(), QStringLiteral("browser")));
        QVERIFY(!IfbaAppSearch::matchesDescription(QStringLiteral("A browser"), QString()));
    }
};

QTEST_GUILESS_MAIN(DescriptionMatcherTest)
#include "DescriptionMatcherTest.moc"
