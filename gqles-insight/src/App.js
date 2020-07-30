import React, { useState } from 'react';

import { ApolloClient, ApolloProvider, InMemoryCache, useQuery } from '@apollo/client';
import { ApolloLink } from 'apollo-link';
import { RetryLink } from 'apollo-link-retry';
import { HttpLink } from 'apollo-link-http';

import { loader } from 'graphql.macro';

import { withStyles } from '@material-ui/core/styles';

import Accordion from '@material-ui/core/Accordion';
import AccordionDetails from '@material-ui/core/AccordionDetails';
import AccordionSummary from '@material-ui/core/AccordionSummary';
import AccordionActions from '@material-ui/core/AccordionActions';
import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ClickAwayListener from '@material-ui/core/ClickAwayListener';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Grid from '@material-ui/core/Grid';
import IconButton from '@material-ui/core/IconButton';
import Link from '@material-ui/core/Link';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemAvatar from '@material-ui/core/ListItemAvatar';
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import ListItemText from '@material-ui/core/ListItemText';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import SearchIcon from '@material-ui/icons/Search';
import Skeleton from '@material-ui/lab/Skeleton';
import SvgIcon from '@material-ui/core/SvgIcon';
import Typography from '@material-ui/core/Typography';

import { Router, Link as RouterLink, useMatch } from "@reach/router";

import copy from 'clipboard-copy';
import TimeAgo from 'react-timeago';

import DelayedRender from './DelayedRender';
import JSONView, { loadB64JSONOrNothing } from './JSONTree.js';


const client = new ApolloClient({
    cache: new InMemoryCache(),
    link: ApolloLink.from([
        new RetryLink(),
        new HttpLink({ uri: 'http://localhost:8000/graphql/' })
    ]),
});


const GetNotificationsQuery = loader(
    './GetNotifications.graphql');

const GetEventContextQuery = loader(
    './GetEventContext.graphql');

const GetEventLogQuery = loader(
    './GetEventLog.graphql');



function FriendlyTimeAgo({ date }) {
    const [friendly, setFriendly] = useState(true);

    return (date === undefined ? (
        <Skeleton width="7em" />
    ) : friendly ? (
        <Link
          color="inherit"
          fontSize="inherit"
          onClick={() => setFriendly(!friendly)}
        >
          <TimeAgo date={date} />
        </Link>

    ) : (
        <ClickAwayListener onClickAway={() => setFriendly(!friendly)}>
          <Box component="span" fontFamily="Monospace">
            {date}
          </Box>
        </ClickAwayListener>
    ));
}




function FriendlyList({children, empty, ...props}) {
    return (
        !Array.isArray(children) || children.length ?
            <List {...props}>
              {children}
            </List>
        : <DelayedRender>
            <Box m={4}>
              {empty ||
               <Grid spacing={2} container direction="row" alignItems="center" justify="center">
                 <Grid item container xs={12} justify="center">
                   <SearchIcon fontSize="large" />
                 </Grid>
                 <Grid item>
                   There is nothing here.
                 </Grid>
               </Grid>
              }
            </Box>
          </DelayedRender>
    );
}

function EventTopic({ event }) {
    return (event ? (
        <Box component="span" fontFamily="Monospace">
          {event.topic}
        </Box>
    ) : (
        <Skeleton width="25em"/>
    ));
}

function EventLink({ applicationName, event }) {

    if (event === undefined ||
        event.originatorId === undefined ||
        event.originatorVersion === undefined
       ) {
        return <Skeleton width="25em"/>;
    }

    const idversion = `${event.originatorId}/${event.originatorVersion}`;
    const nameidversion = applicationName && `${applicationName}/${idversion}`;
    const fullpath = nameidversion && `/event/${nameidversion}/${nameidversion}`;

    return (
        <span style={{
            display: 'flex',
            alignItems: 'center'
        }}>
          <IconButton
            aria-label="clipboard"
            size="small"
            onClick={() => copy(nameidversion || idversion)}
          >
            <SvgIcon fontSize="inherit">
              <path d="M19 2h-4.18C14.4.84 13.3 0 12 0c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z"/>
            </SvgIcon>
          </IconButton>
          <Box component="span" fontFamily="Monospace">
            {fullpath !== undefined ? (
                <Link
                  component={RouterLink}
                  to={fullpath}
                >
                  {nameidversion}
                </Link>
            ) : nameidversion || idversion}
          </Box>
        </span>
    );
}

function EventListItem({ applicationName, event, noExpand }) {

    const idversion = event && `${event.originatorId}/${event.originatorVersion}`;
    const nameidversion = applicationName && event && `${applicationName}/${idversion}`;

    const match = useMatch(nameidversion || 'this-does-not-exist');

    return (
        <ListItem alignItems="flex-start" selected={!!match} >
          <ListItemAvatar>{applicationName !== undefined ? (
              <Avatar alt={applicationName} >
                {applicationName.substring(0, 2).toUpperCase()}
              </Avatar>
          ) : <Skeleton variant="circle" width={40} height={40} />}
          </ListItemAvatar>
          <ListItemText
            primary={<EventTopic event={event} />}
            secondary={
                <>
                  <EventLink
                    applicationName={applicationName}
                    event={event}
                  />
                  <FriendlyTimeAgo date={event && event.timestamp} />
                </>
            }
          />
          {!noExpand && nameidversion && (
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="more"
                  component={RouterLink}
                  to={nameidversion}
                >
                  <NavigateNextIcon />
                </IconButton>
              </ListItemSecondaryAction>
          )}
        </ListItem>

    );
}

const FixedAccordionSummary = withStyles({
    content: {
        minWidth: 0,
    },
})(AccordionSummary);

function EventWithContext({
    applicationName, originatorId, originatorVersion
}) {

    // TODO: In some cases we already have partial data in cache before
    // we fire the request. Take that into account.


    const { error, data, loading } = useQuery(GetEventContextQuery, {
        variables: {
            applicationName,
            originatorId,
            originatorVersion,
        }
    });

    const event = data && data.event;

    return (
        <Box m={2}>

          <Typography variant="subtitle1" component="h2">
            <EventTopic event={event} />
          </Typography>

          <EventLink
            applicationName={applicationName}
            event={event}
          />
          <Typography variant="body2" color="textSecondary">
            <FriendlyTimeAgo date={event && event.timestamp} />
          </Typography>

          <Box my={2}>
            {event && event.stateInsight.filter(stateInsight => ![
                "timestamp",
                "originator_id",
                "originator_version",
                "originator_topic",
            ].includes(stateInsight.key)).map(((stateInsight, i) => (
                <Accordion key={i}>
                  <FixedAccordionSummary
                    style={{minWidth: 0}}
                    expandIcon={<ExpandMoreIcon />}
                    style={{userSelect: 'text'}}
                  >
                    <Grid container my={2} spacing={2}>
                      {/* We're disabling click & focus on the fields, */}
                      {/* we want to provide easy selection of keys & values. */}

                      <Grid item xs={4} >
                        <Typography noWrap>
                          <Box
                            component="span"
                            fontFamily="Monospace"
                            style={{
                                userSelect: "all",
                            }}
                            onClick={(event) => event.stopPropagation()}
                            onFocus={(event) => event.stopPropagation()}
                          >
                            {stateInsight.key}
                          </Box>
                        </Typography>
                      </Grid>

                      <Grid item xs={8}>
                        <Typography noWrap color="textSecondary">
                          <Box
                            component="span"
                            fontFamily="Monospace"
                            style={{
                                userSelect: "all",
                            }}
                            onClick={(event) => event.stopPropagation()}
                            onFocus={(event) => event.stopPropagation()}
                          >
                            {stateInsight.text}
                          </Box>
                        </Typography>
                      </Grid>

                    </Grid>

                  </FixedAccordionSummary>

                  {/* TODO: We want an api we can pass the uuids to and it tells us if it is anything usefull. Basically matching app, and returning position 0. */}

                  <AccordionDetails>
                    <JSONView
                // FIXME: We should catch errors from JSON.parse!
                      data={{[stateInsight.key]: (
                          stateInsight.json ? JSON.parse(stateInsight.json)
                              : stateInsight.text
                      )}}
                      hideRoot={true}
                      sortObjectKeys={true}
                      shouldExpandNode={(keyName, data, level) => level < 2}
                    />
                  </AccordionDetails>
                </Accordion>

            )))}
          </Box>

          <EventLog
            applicationName={applicationName}
            originatorId={originatorId}
            originatorVersion={originatorVersion}
            noExpand
          />

        </Box>
    );

}


function EventRouteComponent({
    applicationName, originatorId, originatorVersionString
}) {
    return (
        <EventWithContext
          applicationName={applicationName}
          originatorId={originatorId}
          originatorVersion={parseInt(originatorVersionString, 10)}
        />
    );

}

function NotificationLog() {
    const [selection, setSelection] = useState(undefined);

    const { error, data, loading } = useQuery(GetNotificationsQuery, {
        pollInterval: 5000,
        onCompleted: ({ applications }) => {
            setSelection(applications.map(({ name }) => (
                // Take default values from existing selection.
                (selection || []).find(([k, s]) => k === name) || [name, false]
            )));
        },
    });

    const notifications = data && data.notifications;

    // <Grid item xs={2}>
    //   <Menu selection={selection} setSelection={setSelection} />
    // </Grid>

    return (
        <FriendlyList
          component="nav"
          aria-label="notifications"
        >
          {notifications !== undefined ? notifications.edges.map(edge => (
              <EventListItem
                key={edge.cursor}
                applicationName={edge.application && edge.application.name}
                event={edge.node.event}
              />
          )).reverse() : <DelayedRender>{[1, 2, 3].map((key) => (
              <EventListItem key={key} />
          ))}</DelayedRender>}
        </FriendlyList>
    );
}

function EventLog({
    applicationName, originatorId, originatorVersion, noExpand
}) {

    //  TODO: The current event is probably in cache, we should get it!

    const [showLaterEvents, setShowLaterEvents] = useState(false);

    const { error, data, loading } = useQuery(GetEventLogQuery, {
        pollInterval: 5000,
        variables: {
            applicationName,
            originatorId,
            originatorVersion,
        }
    });

    if (data && data.event === null) {
        return (
            // TODO: Better message!
            <p>There is no data for this event. </p>
        );
    }

    const edges = data && data.event && [
        ...data.event.previousEvents.edges,
        {
            cursor: "current",
            node: {
                ...data.event,
                // No point in keeping those around!
                previousEvents: [],
                nextEvents: [],
            }
        },
        ...data.event.nextEvents.edges,
    ];

    return (
        <FriendlyList
          component="nav"
          aria-label="notifications"
        >
          {edges !== undefined ? edges.map(edge => (
              <EventListItem
                key={edge.cursor}
                applicationName={applicationName}
                event={edge.node}
                noExpand={noExpand}
              />
          )).reverse() : <DelayedRender>{[1, 2, 3].map((key) => (
              <EventListItem key={key} />
          ))}</DelayedRender>}
        </FriendlyList>
    );

}

function SplitPane({ children }) {
    return (
        <Grid container>
          {children.map((child, i) => (
              <Grid key={i} item md={6} >
                {child}
              </Grid>
          ))}
        </Grid>
    );
}

function EventLogRouteComponent({
    applicationName, originatorId, originatorVersionString
}) {
    return (
        <SplitPane>
          <EventLog
            applicationName={applicationName}
            originatorId={originatorId}
            originatorVersion={parseInt(originatorVersionString, 10)}
          />
          <Router>
            <EventRouteComponent
              path=":applicationName/:originatorId/:originatorVersionString"
            />
          </Router>
        </SplitPane>
    );
}

function NotificationLogRouteComponent() {
    //  Here we will parse application names from the url filter if any.
    return (
        <SplitPane>
          <NotificationLog />
          <Router>
            <EventRouteComponent
              path=":applicationName/:originatorId/:originatorVersionString"
            />
          </Router>
        </SplitPane>
    );
}

function App() {
    return (
        <>
          <Box mt={2} mx={2}>
            <Button
              variant="text"
              color="primary"
              startIcon={<ChevronLeftIcon/>}
              component={RouterLink}
              to="/notifications/"
            >
              all notifications
            </Button>
          </Box>

          {/* TODO: We actually want to have both panes be handled by the same component. */}
          {/* The opposite of what we have now, one use case: */}
          {/* - prev/next buttons above the right pane's context, navigating in the right pane. */}

          {/* Also, that way we can have the left-list be md=5 and xs=hidden when no space because of right pane, until right pane is closed. */}

          {/* TODO: Add close button for right pane in that case. */}

          <Router>
            <NotificationLogRouteComponent
              path="/notifications/*"
            />
            <EventLogRouteComponent
              path="/event/:applicationName/:originatorId/:originatorVersionString/*"
            />
          </Router>
        </>
    );
}


function AppWithProviders() {
    return (
        <ApolloProvider client={client}>
          <App />
        </ApolloProvider>
    );
}

export default AppWithProviders;
